import streamlit as st
from crew.mode3_crew import render_mode_3
from llm.debater import generate_team_line


st.title("AI Debate Sparring Partner — Demo")

motion_text = st.text_input("Enter the motion")

stance = st.selectbox("Pick your stance", options=["affirmative", "negative"])
speaker_role = st.selectbox("Pick your speaker role", options=[1, 2, 3])
team_line = st.text_input("Enter your team line")

if st.button("Start Debate"):
    st.session_state.debate_started = True
    st.session_state.team_lines = {
        stance: team_line,
        ("negative" if stance == "affirmative" else "affirmative"): generate_team_line(
            "negative" if stance == "affirmative" else "affirmative", motion_text
        )
    }

if st.session_state.get("debate_started"):
    render_mode_3(stance, speaker_role, st.session_state.team_lines)