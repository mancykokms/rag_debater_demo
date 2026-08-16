import streamlit as st
from crew.agents import run_arguments_crew, run_rebuttals_crew, run_judge_crew
from llm.debater import get_next_speaker, generate_team_line
from utils.diff import safe_display


async def render_mode1():

    st.subheader("Mode 1 (CrewAI) — Demo")

    motion_text = st.text_input("Enter the motion")
    
    stance = st.selectbox("Pick your stance", options=["affirmative", "negative"])
    speaker_role = st.selectbox("Pick your speaker role", options=[1, 2, 3])
    team_line = st.text_input("Enter your team line")
    
    if st.button("Start Debate"):
        if not team_line.strip():
            st.warning("Please enter your teamline before starting. ")
        else:
            st.session_state.debate_started = True
            st.session_state.team_lines = {
                stance: team_line,
                ("negative" if stance == "affirmative" else "affirmative"): generate_team_line(
                    "negative" if stance == "affirmative" else "affirmative", motion_text
                )
            }
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    student_speech = st.chat_input("Write your speech", key="mode1_chat_input")

    if student_speech:
        if not team_line.strip():
            st.warning("Please enter your team line before starting.")
            return

        st.session_state.messages.append({"role": "user", "content": student_speech})
        with st.chat_message("user"):
            st.write(student_speech)

        next_speaker = get_next_speaker(stance, speaker_role)

        if next_speaker is not None:
            next_speaker_stance, next_speaker_role = next_speaker
            opponent_team_line = team_line_affirmative if next_speaker_stance == "affirmative" else team_line_negative
            need_rebuttals = not (next_speaker_role == 1 and next_speaker_stance == "affirmative")

            opponent_response = await run_arguments_crew(
                team_line=opponent_team_line,
                speaker_role=next_speaker_role,
                stance=next_speaker_stance,
                mode="opponent",
                need_rebuttals=need_rebuttals
            )
            opponent_text = opponent_response.raw
            if need_rebuttals and "{rebuttals}" in opponent_text:
                rebuttal_text = await run_rebuttals_crew(
                    speech_so_far=student_speech,
                    team_line=opponent_team_line,
                    speaker_role=next_speaker_role,
                    stance=next_speaker_stance,
                    mode="opponent"
                )
                opponent_text = opponent_text.replace("{rebuttals}", rebuttal_text.raw)
            opponent_text = opponent_text.replace("{rebuttals}", " ").strip()

            with st.chat_message("opponent"):
                st.write(safe_display(opponent_text))
        else:
            st.info("This was the final speech of the round — no more rebuttals.")

        feedback = await run_judge_crew(
                student_speech=student_speech,
                speaker_role=speaker_role,
                stance=stance,
                team_line=team_line
            )

        with st.chat_message("judge"):
            if "error" in feedback:
                st.error(f"Judge feedback couldn't be parsed. Raw response: {feedback['raw_text']}")
            else:
                st.markdown(f"**Summary:** {feedback['summary_feedback']}")
                st.markdown("**Scores:**")
                for category, score in feedback['role_specific_score'].items():
                    st.metric(category.replace('_', ' ').title(), f"{score}/10")
                if feedback.get('unaddressed_points'):
                    st.markdown("**Unaddressed points:**")
                    for point in feedback['unaddressed_points']:
                        st.markdown(f"- {point}")
