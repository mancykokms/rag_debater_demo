import streamlit as st
from ingest.team_setup import render_team_setup, get_teachers_sheet
from ingest.manage_pools import get_students_sheet, get_teams_sheet, add_student, add_coach_to_existing_team, get_teachers_sheet, get_team_id
from ingest.ingest_motion import get_motions_sheet, create_motion
from ingest.assign_squad import (
    get_squads_sheet,
    debate_assemble,
)


st.title("Login Page")

if not st.user.is_logged_in:
    st.write("You are not logged in.")
    if st.button("Log in with Google"):
        st.login()
else:
    st.write(f"Logged in as: {st.user.email}")
    render_team_setup()
    
    st.divider()
    st.header("Test: Add Students")
    add_student(get_students_sheet())
    
    st.divider()
    st.header("Test: Add Coach")
    add_coach_to_existing_team(get_teachers_sheet())
    
    st.divider()
    st.header("Test: Create Motion")
    create_motion(get_motions_sheet())

# Add this to visually confirm session_state actually persisted:
    if "current_motion_id" in st.session_state:
        st.write("Current motion_id in session_state:", st.session_state.current_motion_id)
        
    st.divider()
    st.header("Test: Assign Squad")
    team_id = get_team_id()
    if team_id:
        debate_assemble(
            team_id,
            get_motions_sheet(),
            get_students_sheet(),
            get_teachers_sheet(),
            get_squads_sheet(),
        )
    else:
        st.info("Create or join a team first.")
    
    
    if st.button("Log out"):
        st.logout()