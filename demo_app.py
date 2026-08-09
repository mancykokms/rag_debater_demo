import streamlit as st
from crew.mode2_crew import render_mode_3
from llm.debater import generate_team_line
import uuid
import asyncio


st.title("AI Debate Sparring Partner — Mode 2 Demo")

motion_text = st.text_input("Enter the motion")

stance = st.selectbox("Pick your stance", options=["affirmative", "negative"])
speaker_role = st.selectbox("Pick your speaker role", options=[1, 2, 3])
team_line = st.text_input("Enter your team line")

MOTION_ID = "esports_schools_demo"  # a stable, unique string for THIS motion — not "test_motion"
TEAM_ID = "demo_team"

if st.button("Start Debate"):
    st.session_state.debate_started = True
    st.session_state.team_lines = {
        stance: team_line,
        ("negative" if stance == "affirmative" else "affirmative"): generate_team_line(
            "negative" if stance == "affirmative" else "affirmative", motion_text
        )
    }
    st.write("DEBUG team_lines:", st.session_state.team_lines)  # temporary

if st.session_state.get("debate_started"):
    asyncio.run(render_mode_3(stance, speaker_role, st.session_state.team_lines))