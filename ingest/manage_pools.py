import streamlit as st
from ingest.open_sheet import open_spreadsheet
from ingest.team_setup import find_existing_team_by_domain, get_domain, get_teams_sheet

@st.cache_resource
def get_students_sheet():
    return open_spreadsheet().worksheet("student_pool")

def get_team_id():
    domain = get_domain(st.user.email)
    teams_sheet = get_teams_sheet()
    return find_existing_team_by_domain(domain, teams_sheet)

def parse_student_list(raw_input):
    students = []
    lines = raw_input.split("\n")
    for line in lines:
        if not line.strip():
            continue
        parts = line.split(";")
        if len(parts) != 2:
            st.error(f"Cannot parse this line: {line}")
            continue
        that_one_dict = {"name": parts[0].strip(), "email": parts[1].strip()}
        students.append(that_one_dict)
    return students
        
        
        
    
def add_student(students_sheet):
    raw_input = st.text_area("Input students, one per each line", 
                             placeholder="Alice Chan; alice@school.edu.hk \nBob Wong; bob@school.edu.hk")
    if st.button("Parse students"):
        st.session_state.parsed_students = parse_student_list(raw_input)
    if "parsed_students" in st.session_state:
        student_list = st.session_state.parsed_students
        st.write("The students are: ", student_list)
        if st.button("Add students"):
            try:
                for student in student_list:
                    students_sheet.append_row([get_team_id(), student["name"], student["email"]])
                st.success(f"Students added successfully!")
                del st.session_state["parsed_students"]
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add students: {e}")
                
def add_coach_to_existing_team(teams_sheet):
    team_id = get_team_id()
    row = teams_sheet.find(team_id)
    teacher_emails = teams_sheet.cell(row.row, 3).value
    teacher_emails = teacher_emails.split(";")
    teacher_emails = [e.strip() for e in teacher_emails]
    new_email = st.text_input("Input new coach's email")
    if new_email not in teacher_emails:
        teacher_emails.append(new_email)
        updated_emails = "; ".join(teacher_emails)
        teams_sheet.update_cell(row.row, 3, updated_emails)
    else:
        st.error("This coach already exists in your team. ")
        
        
    

    
        
        
        
        
    
    