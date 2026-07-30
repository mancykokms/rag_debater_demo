import streamlit as st
from ingest.open_sheet import open_spreadsheet
from ingest.team_setup import find_existing_team_by_domain, get_domain, get_teams_sheet
from ingest.team_setup import parse_teacher_list, get_teachers_sheet

@st.cache_resource
def get_students_sheet():
    return open_spreadsheet().worksheet("student_pool")

@st.cache_data(ttl=300)
def get_team_id():
    domain = get_domain(st.user.email)
    teachers_sheet = get_teachers_sheet()
    return find_existing_team_by_domain(domain, teachers_sheet)

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
                
def add_coach_to_existing_team(teachers_sheet):
    team_id = get_team_id()
    raw_input = st.text_area("Input teachers, one per each line", 
                            placeholder="Alice Chan; alice@school.edu.hk \nBob Wong; bob@school.edu.hk")
    if st.button("Parse teachers"):
        st.session_state.parsed_teachers = parse_teacher_list(raw_input)
    if st.session_state.get("just_added"): 
        st.success(f"teachers added successfully!")
        del st.session_state["just_added"]
    if "parsed_teachers" in st.session_state:
        teacher_list = st.session_state.parsed_teachers
        st.write("The coaches are: ", teacher_list)
        if st.button("Add coach"):
            try:
                for teacher in teacher_list:
                    teachers_sheet.append_row([team_id, teacher["name"], teacher["email"]])
                st.session_state.just_added = True
                del st.session_state["parsed_teachers"]
                st.rerun()
            except Exception as e:
                st.error(f"Failed to add teachers: {e}")
  
            
        
    

    
        
        
        
        
    
    