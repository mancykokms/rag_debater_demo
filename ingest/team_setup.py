import streamlit as st
from ingest.open_sheet import open_spreadsheet
import uuid

@st.cache_resource
def get_teams_sheet():
    return open_spreadsheet().worksheet("teams")

def get_domain(email):
    return email.split("@")[-1].lower()

def find_existing_team_by_domain(domain, teams_sheet):
    all_teams = teams_sheet.get_all_records()
    for team in all_teams:
        existing_emails = team["teacher_emails"].split(";")
        existing_domains = [get_domain(e.strip()) for e in existing_emails]
        if domain in existing_domains:
            return team["team_id"]
    return None

def add_team(domain, teams_sheet):
    team_id = find_existing_team_by_domain(domain, teams_sheet)
    if not team_id:
        school_name = st.text_input("school name")
        teacher_emails = st.multiselect("Add teacher emails", 
                                        options=[st.user.email], 
                                        accept_new_options=True, 
                                        placeholder="Type an email and press Enter")
        st.write("The coaches are: ", teacher_emails)
        team_id = str(uuid.uuid4().hex[:8])
        if st.button("Create school"):
            try:
                teams_sheet.append_row([team_id, school_name, "; ".join(teacher_emails)])
                st.success(f"Team {team_id} created successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create team: {e}")
    else:
        st.info(f"You're already part of team {team_id}.")

def render_team_setup():
    st.title("Team Setup")
    domain = get_domain(st.user.email)
    add_team(domain, get_teams_sheet())
    



