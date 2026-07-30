import streamlit as st
from ingest.open_sheet import open_spreadsheet
import uuid

@st.cache_resource
def get_teams_sheet():
    return open_spreadsheet().worksheet("teams")

@st.cache_resource
def get_teachers_sheet():
    return open_spreadsheet().worksheet("teachers")

def get_domain(email):
    return email.split("@")[-1].lower()

@st.cache_data(ttl=300)
def find_existing_team_by_domain(domain, _teachers_sheet):
    all_teachers = _teachers_sheet.get_all_records()
    for teacher in all_teachers:
        existing_email = teacher["teacher_email"]
        existing_domain = get_domain(existing_email)
        if domain == existing_domain:
            return teacher["team_id"]
    return None

def parse_teacher_list(raw_input):
    teachers = []
    lines = raw_input.split("\n")
    for line in lines:
        if not line.strip():
            continue
        parts = line.split(";")
        if len(parts) != 2:
            st.error(f"Cannot parse this line: {line}")
            continue
        that_one_dict = {"name": parts[0].strip(), "email": parts[1].strip()}
        teachers.append(that_one_dict)
    return teachers

def add_team(domain, teams_sheet, teachers_sheet):
    team_id = find_existing_team_by_domain(domain, teachers_sheet)
    if not team_id:
        school_name = st.text_input("school name")
        # teacher_emails = st.multiselect("Add teacher emails", 
        #                                 options=[st.user.email], 
        #                                 accept_new_options=True, 
        #                                 placeholder="Type an email and press Enter")
        raw_input = st.text_area("Input teachers, one per each line", 
                                     placeholder="Alice Chan; alice@school.edu.hk \nBob Wong; bob@school.edu.hk")
        if st.button("Parse teachers"):
            st.session_state.parsed_teachers = parse_teacher_list(raw_input)
        if "parsed_teachers" in st.session_state:
            teacher_list = st.session_state.parsed_teachers
            st.write("The coaches are: ", teacher_list)
        team_id = str(uuid.uuid4().hex[:8])
        if st.button("Create school"):
            try:
                for teacher in teacher_list:
                    teachers_sheet.append_row([team_id, teacher["name"], teacher["email"]])
                st.success(f"teachers added successfully!")
                del st.session_state["parsed_teachers"]
                teams_sheet.append_row([team_id, school_name])
                st.success(f"Team {team_id} created successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to create team: {e}")
    else:
        st.info(f"You're already part of team {team_id}.")

def render_team_setup():
    st.title("Team Setup")
    domain = get_domain(st.user.email)
    add_team(domain, get_teams_sheet(), get_teachers_sheet())
    



