from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import streamlit as st
from pydantic import BaseModel
from typing import Dict, List
from llm.debater import build_system_prompt, ROLE_LABELS, ROLE_STANCE_INSTRUCTIONS, MODE_INSTRUCTIONS, generate_team_line
from llm.judge import build_judge_prompt
from utils.diff import safe_display
from crew.mode2_crew import FULL_ROUND_SEQUENCE
import asyncio

provider = OpenAIProvider(
    base_url="https://token.sensenova.cn/v1",
    api_key=st.secrets["sensenova"]["api_key"],
)

model = OpenAIChatModel("sensenova-6.8-flash-lite", provider=provider)



class JudgeFeedback(BaseModel):
    role_specific_score: Dict[str, int]
    unaddressed_points: List[str]
    fallacies_or_gaps: List[str]
    strengths: List[str]
    summary_feedback: str
    
    
class DebaterResponse(BaseModel):
    speech_text: str
    sources_cited: List[str]

    
judge_agent = Agent(model, output_type=JudgeFeedback)   
debater_agent = Agent(model)

@judge_agent.tool_plain
@debater_agent.tool_plain
def web_search(query: str) -> str:
    """Search the web for real, current information on a topic."""
    from rag.web_search import web_search as do_search
    results = do_search(query)
    return "\n\n".join([f"{r['title']} ({r['url']}): {r['content']}" for r in results])

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_RETRY_ATTEMPTS = 4
RETRY_BASE_DELAY_SECONDS = 2.0

async def run_agent_with_retry(agent, user_message, instructions):
    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            return await agent.run(user_message, instructions=instructions)
        except ModelHTTPError as e:
            if e.status_code not in RETRYABLE_STATUS_CODES or attempt == MAX_RETRY_ATTEMPTS:
                raise
            delay = RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1))
            st.warning(
                f"Model is busy (HTTP {e.status_code}). Retrying in {delay:.0f}s... (attempt {attempt}/{MAX_RETRY_ATTEMPTS})"
            )
            await asyncio.sleep(delay)

async def generate_debater_response(team_line, speaker_role, stance, mode, student_speech=None):
    system_prompt = build_system_prompt(speaker_role, stance, mode)
    if student_speech:
        user_message = f"Your team's case line \n{team_line}\n search the web for real and current evidence to respond to: \n{student_speech}. "
    else:
        user_message = f"Your team's case line \n{team_line}\n search the web for real and current evidence to support your opening speech. "
    response = await run_agent_with_retry(debater_agent, user_message, system_prompt)
    return response.output

async def generate_judge_response(student_speech, speaker_role, stance, team_line):
    judge_prompt = build_judge_prompt(speaker_role, stance)

    user_message = f"The case line is \n{team_line}\n search the web for real, current evidence and judge the student's speech \n{student_speech}\n with reference to their opponent"
    response = await run_agent_with_retry(judge_agent, user_message, judge_prompt)
    return response.output

def get_preceding_speaker(speaker_role, stance):
    if speaker_role == 1 and stance == "affirmative":
        return None
    if stance == "negative":
        return (speaker_role, "affirmative")
    return (speaker_role - 1, "negative")

def get_following_speaker(speaker_role, stance):
    if speaker_role == 3 and stance == "negative":
        return None
    if stance == "affirmative":
        return (speaker_role, "negative")
    return (speaker_role + 1, "affirmative")

def render_mode1_message(msg):
    if msg["role"] == "judge":
        feedback = msg["feedback"]
        with st.chat_message("judge", avatar=msg["avatar"]):
            st.markdown(f"**Summary:** {feedback.summary_feedback}")
            st.markdown("**Scores:**")
            score_cols = st.columns(3)
            for i, (category, score) in enumerate(feedback.role_specific_score.items()):
                with score_cols[i % 3]:
                    st.metric(category.replace('_', ' ').title(), f"{score}/10")
            if feedback.unaddressed_points:
                st.markdown("**Unaddressed points:**")
                for point in feedback.unaddressed_points:
                    st.markdown(f"- {point}")
    else:
        with st.chat_message(msg["role"], avatar=msg["avatar"]):
            st.write(safe_display(msg["text"]))


def mode1_render():
    st.subheader("Mode 1 (Pydantic AI) - Demo")
    motion_text = st.text_input("Enter the motion", key="mode1_motion")
    stance = st.selectbox("Pick your stance", options=["affirmative", "negative"], key="mode1_stance")
    speaker_role = st.selectbox("Pick your speaker role", options=[1, 2, 3], key="mode1_role")
    team_line = st.text_input("Enter your team line", key="mode1_team_line")

    if st.button("Start Debate", key="mode1_start"):
        if not team_line.strip():
            st.warning("Please enter your teamline before starting. ")
        else:
            st.session_state.mode1_started = True
            st.session_state.mode1_submitted = False
            st.session_state.mode1_completed = False
            st.session_state.mode1_debate_speaker_role = speaker_role
            st.session_state.mode1_debate_stance = stance
            st.session_state.mode1_debate_team_line = team_line
            st.session_state.mode1_team_lines = {
                stance: team_line,
                ("negative" if stance == "affirmative" else "affirmative"): generate_team_line(
                    "negative" if stance == "affirmative" else "affirmative", motion_text
                )
            }
            st.session_state.mode1_history = []

            preceding_speaker = get_preceding_speaker(speaker_role, stance)
            if preceding_speaker:
                preceding_role, preceding_stance = preceding_speaker
                preceding_team_line = st.session_state.mode1_team_lines[preceding_stance]
                with st.spinner("Generating speech..."):
                    preceding_speech = asyncio.run(
                        generate_debater_response(
                            preceding_team_line, preceding_role, preceding_stance, "opponent"
                        )
                    )
                st.session_state.mode1_history.append(
                    {"role": "assistant", "avatar": "🥷", "text": preceding_speech}
                )

    if not st.session_state.get("mode1_started"):
        return

    for msg in st.session_state.mode1_history:
        render_mode1_message(msg)

    speaker_role = st.session_state.mode1_debate_speaker_role
    stance = st.session_state.mode1_debate_stance
    team_line = st.session_state.mode1_debate_team_line

    if not st.session_state.get("mode1_submitted"):
        student_speech = st.chat_input("Write your speech", key="mode1_student_speech")
        if student_speech:
            st.session_state.mode1_submitted = True
            st.session_state.mode1_current_student_speech = student_speech
            st.session_state.mode1_history.append(
                {"role": "student", "avatar": "👤", "text": student_speech}
            )
            st.rerun()
        return

    if st.session_state.get("mode1_completed"):
        return

    student_speech = st.session_state.mode1_current_student_speech

    following_speaker = get_following_speaker(speaker_role, stance)
    if following_speaker:
        following_role, following_stance = following_speaker
        following_team_line = st.session_state.mode1_team_lines[following_stance]
        with st.spinner("Generating speech..."):
            following_speech = asyncio.run(
                generate_debater_response(
                    following_team_line, following_role, following_stance, "opponent",
                    student_speech=student_speech
                )
            )
        following_msg = {"role": "assistant", "avatar": "🥷", "text": following_speech}
        st.session_state.mode1_history.append(following_msg)
        render_mode1_message(following_msg)

    with st.spinner("Judge is evaluating..."):
        feedback = asyncio.run(
            generate_judge_response(
                student_speech, speaker_role, stance, team_line
            )
        )
    judge_msg = {"role": "judge", "avatar": "🧑‍⚖️", "feedback": feedback}
    st.session_state.mode1_history.append(judge_msg)
    render_mode1_message(judge_msg)
    st.session_state.mode1_completed = True
if __name__ == "__main__":
    feedback = asyncio.run(generate_judge_response(
        student_speech="We believe carbon taxes are necessary because they create a direct financial incentive to reduce emissions.",
        speaker_role=1,
        stance="affirmative",
        team_line="We support carbon taxes because they create market incentives that drive innovation and emissions reduction."
    ))
    print("Score:", feedback.role_specific_score)
    print("Unaddressed:", feedback.unaddressed_points)
    print("Summary:", feedback.summary_feedback)
