from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from typing import TypedDict, Annotated
import operator
from langchain_openai import ChatOpenAI
import streamlit as st
import httpx
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage
from llm.debater import ROLE_LABELS, ROLE_STANCE_INSTRUCTIONS, format_transcript, generate_team_line
from llm.judge import JUDGE_ROLE_CRITERIA, JUDGE_SYSTEM_PROMPT_TEMPLATE, build_judge_prompt 
import json
from crew.agents import ARGUMENT_CHECKLISTS, ARGUMENT_WORD_LIMITS, REBUTTAL_CHECKLISTS
import uuid
from utils.diff import safe_display

class DebateState(TypedDict):
    student_stance: str
    team_lines: dict[str, str]
    speeches: Annotated[list[dict], operator.add]
    student_speech: str
    current_index: int
    judge_feedback: list[dict]

# custom_client = httpx.Client(verify=True)
llm = ChatOpenAI(
    model="sensenova-6.8-flash-lite",
    base_url="https://token.sensenova.cn/v1",
    api_key=st.secrets["sensenova"]["api_key"],
    max_tokens=600,
    extra_body={"reasoning_effort": "none"},
    # http_client=custom_client,
)

judge_llm = ChatOpenAI(
    model="sensenova-6.8-flash-lite",
    base_url="https://token.sensenova.cn/v1",
    api_key=st.secrets["sensenova"]["api_key"],
    max_tokens=1500,
    extra_body={"reasoning_effort": "none"},
)

    
FULL_ROUND_SEQUENCE = [
    (1, "affirmative"), 
    (1, "negative"),
    (2, "affirmative"),
    (2, "negative"),
    (3, "affirmative"),
    (3, "negative")
]

def build_system_prompt(speaker_role, stance, mode):
    role = (speaker_role, stance)
    instructions = ROLE_STANCE_INSTRUCTIONS[role]
    system_prompt = instructions
    return system_prompt


@tool
def web_search(query: str) -> str:
    """Search the web for real, current information on a topic"""
    from rag.web_search import web_search
    results = web_search(query)
    return "\n\n".join([f"{r['title']} ({r['url']}): {r['content']}" for r in results])


def route_next(state: DebateState) -> str:
    if state["current_index"] >= len(FULL_ROUND_SEQUENCE):
        return "judge"
    current_stance = FULL_ROUND_SEQUENCE[state["current_index"]][1]
    if current_stance == state["student_stance"]:
        return "student_turn"
    else:
        return "generate_speech"
    
def student_turn(state: DebateState) -> DebateState:
    role = (state["current_index"] // 2) + 1
    student_input = interrupt(f"Write your speech as speaker {role}")
    speech = {"stance": state["student_stance"], "speaker_role": role, "text": student_input}
    
    return {
        "speeches": [speech],
        "current_index": state["current_index"] + 1
    }
    

def generate_speech(state: DebateState) -> DebateState:
    role = (state["current_index"] // 2) + 1
    stance = FULL_ROUND_SEQUENCE[state["current_index"]][1]
    team_line = state["team_lines"][stance]
    transcript_so_far = format_transcript(state["speeches"])
    
    system_prompt = build_system_prompt(role, stance, "opponent")
    word_limit = ARGUMENT_WORD_LIMITS[role]
    checklist = ARGUMENT_CHECKLISTS[(role, stance)]
    
    needs_rebuttal = not (role == 1 and stance == "affirmative")
    rebuttal_note = REBUTTAL_CHECKLISTS[role] if needs_rebuttal else ""
    
    task_instruction = (
        f"Your team's case line is: \n{team_line}\n\n"
        f"Full round so far: \n{transcript_so_far}\n\n"
        f"Search the web for real current evidence before writing. "
        f"Write your speech in under {word_limit} words. "
        f"{checklist} {rebuttal_note}"
    )
    
    llm_with_tools = llm.bind_tools([web_search])
    messages = [HumanMessage(content=f"{system_prompt}\n\n{task_instruction}")]
    
    while True:
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        
        if not response.tool_calls:
            break
        
        for tool_call in response.tool_calls:
            result = web_search.invoke(tool_call["args"])
            messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))
    
    speech = {"stance": stance, "speaker_role": role, "text": response.content}
        
    return {
        "speeches": [speech],
        "current_index": state["current_index"] + 1
    }
    
def judge_node(state: DebateState) -> DebateState:
    student_speeches = [s for s in state["speeches"] if s["stance"] == state["student_stance"]]
    team_line = state["team_lines"][state["student_stance"]]
    
    feedback_list = []
    
    for speech in student_speeches:
        role = speech["speaker_role"]
        stance = speech["stance"]
        
        judge_prompt = build_judge_prompt(role, stance)
        task_instruction = (
            f"The team's case line:\n{team_line}\n\n"
            f"Search the web for real, current evidence and strong arguments relevant to this motion, "
            f"to identify what points a strong speech should have addressed. \n\n"
            f"Student's speech to judge:\n{speech['text']}\n\n"
            f"Using what you find, evaluate the speech - flag in unaddressed_points any significant "
            f"real evidence or arguments the student did not engage with.\n\n "
            f"Respond with ONLY valid JSON, no preamble, matching exactly this structure: "
            f'{{"role_specific_score": {{...}}, "unaddressed_points": [...], '
            f'"fallacies_or_gaps": [...], "strengths": [...], "summary_feedback": "..."}}'
        )
        llm_with_tools = judge_llm.bind_tools([web_search])
        messages = [HumanMessage(content=f"{judge_prompt}\n\n{task_instruction}")]

        while True:
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            if not response.tool_calls:
                break

            for tool_call in response.tool_calls:
                result = web_search.invoke(tool_call["args"])
                messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))

        try:
            parsed = json.loads(response.content)
        except Exception:
            parsed = {"error": "Could not parse judge response", "raw_text": response.content}
        feedback_list.append(parsed)
        
    return {"judge_feedback": feedback_list}
   
@st.cache_resource   
def graph_initiation():
    graph = StateGraph(DebateState)
    graph.add_node("generate_speech", generate_speech)
    graph.add_node("student_turn", student_turn)
    graph.add_node("judge", judge_node)


    graph.add_conditional_edges(START, route_next)
    graph.add_conditional_edges("generate_speech", route_next)
    graph.add_conditional_edges("student_turn", route_next)

    graph.add_edge("judge", END)

    checkpointer = InMemorySaver()
    return graph.compile(checkpointer=checkpointer)

def mode3_render():
    st.subheader("Mode 3 (Langgraph) - Demo")
    motion_text = st.text_input("Enter the motion", key="mode3_motion")
    stance = st.selectbox("Pick your stance", options=["affirmative", "negative"], key="mode3_stance")
    team_line = st.text_input("Enter your team line", key="mode3_team_line")
    
    if st.button("Start Debate", key="mode3_start_button"):
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
            thread_id = str(uuid.uuid4())
            st.session_state.thread_config = {"configurable": {"thread_id": thread_id}}
            app = graph_initiation()
            
            initial_state = {
                "student_stance": stance,
                "team_lines": st.session_state.team_lines,
                "speeches": [],
                "student_speech": "", 
                "current_index": 0
            }
            st.session_state.graph_result = app.invoke(initial_state, config=st.session_state.thread_config)
            
    if "graph_result" in st.session_state:
        result = st.session_state.graph_result
        
        for speech in result["speeches"]:
            avatar = "🥷" if speech["stance"] != stance else "🧑‍🎓"
            st.chat_message(ROLE_LABELS[(speech["speaker_role"], speech["stance"])], avatar=avatar).write(safe_display(speech["text"]))

        if "__interrupt__" in result:
            student_input = st.chat_input("Write your speech", key="mode3_chat_input")
            if student_input:
                app = graph_initiation()
                st.session_state.graph_result = app.invoke(Command(resume=student_input), config=st.session_state.thread_config)
                st.rerun()
        else:
            for feedback in result.get("judge_feedback", []):
                with st.chat_message("judge", avatar="🧑‍⚖️"):
                    if "error" in feedback:
                        st.error(f"Judge feedback couldn't be parsed. Raw response: {feedback['raw_text']}")
                    else:
                        st.markdown(f"**Summary:** {feedback['summary_feedback']}")
                        st.markdown("**Scores:**")
                        score_cols = st.columns(3)
                        for i, (category, score) in enumerate(feedback['role_specific_score'].items()):
                            with score_cols[i % 3]:
                                st.metric(category.replace('_', ' ').title(), f"{score}/10")
                        if feedback.get('unaddressed_points'):
                            st.markdown("**Unaddressed points:**")
                            for point in feedback['unaddressed_points']:
                                st.markdown(f"- {point}")

    
    


# config = {"configurable": {"thread_id": "test-mode3-1"}}

# initial_state = {
#     "student_stance": "negative",
#     "team_lines": {
#         "affirmative": "We support banning single-use plastics because they cause irreversible environmental harm.",
#         "negative": "We oppose banning single-use plastics because it burdens low-income households."
#     },
#     "speeches": [],
#     "student_speech": "",
#     "current_index": 0
# }

# result = app.invoke(initial_state, config=config)
# print("First invoke result:", result)
    
# result2 = app.invoke(Command(resume="We oppose this ban because it disproportionately harms low-income families who rely on affordable disposable products."), config=config)
# print("After resume:", result2)

# result3 = app.invoke(Command(resume="Our second speaker extends: this ban also disproportionately affects small businesses who cannot absorb the cost of alternatives."), config=config)
# print("After 2nd resume:", result3)

# result4 = app.invoke(Command(resume="Our third and final speaker summarizes: the economic harm to vulnerable communities outweighs the environmental benefits, which can be achieved through better recycling infrastructure instead."), config=config)
# print("After 3rd resume:", result4)