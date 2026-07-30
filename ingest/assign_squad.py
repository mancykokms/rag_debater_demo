import streamlit as st
from ingest.open_sheet import open_spreadsheet

@st.cache_resource
def get_squads_sheet():
    return open_spreadsheet().worksheet("squads")

@st.cache_data(ttl=300)
def get_school_motions(team_id, _motions_sheet):
    all_motions = _motions_sheet.get_all_records()
    school_motions = []
    for motion in all_motions:
        if team_id == motion["team_id"]:
            school_motions.append(motion)
    return school_motions
        

def select_motion(team_id, motions_sheet):
    school_motions = get_school_motions(team_id, motions_sheet)
    if not school_motions:
        st.error("No motions have been created by this school. Please go create one")
    else:
        motion = st.selectbox("Motion", options=school_motions, 
                                placeholder="Select a motion", 
                                format_func=lambda m: m["motion_text"])
        if motion:
            return motion["motion_id"]

@st.cache_data(ttl=300)        
def get_school_students(team_id, _student_pool_sheet):
    student_pool = _student_pool_sheet.get_all_records()
    students = []
    for student in student_pool:
        if team_id == student["team_id"]:
            students.append(student)
    return students

def select_students(team_id, student_pool_sheet):
    students = get_school_students(team_id, student_pool_sheet)
    if not students:
        st.error("No students in this school. Please add students to school before starting a debate. ")
    else:
        col1, col2 = st.columns(2)
        with col1:
            affirmative_speakers = st.multiselect("Affirmative Speakers", options=students, 
                                                placeholder="Select 3 speakers", 
                                                format_func=lambda s: s["student_name"])
            remaining_students = [s for s in students if s not in affirmative_speakers]
        with col2:
            negative_speakers = st.multiselect("Negative Speakers", options=remaining_students, 
                                                        placeholder="Select 3 speakers", 
                                                        format_func=lambda s: s["student_name"])
        if affirmative_speakers and negative_speakers:
            return affirmative_speakers, negative_speakers

@st.cache_data(ttl=300)        
def get_coaches(team_id, _teachers_sheet):
    teachers = _teachers_sheet.get_all_records()
    coaches = []
    for teacher in teachers:
        if team_id == teacher["team_id"]:
            coaches.append(teacher)
    return coaches

def select_coaches(team_id, teachers_sheet):
    coaches = get_coaches(team_id, teachers_sheet)
    if not coaches:
        st.error("This school has no coaches. Please add coaches to school before starting a debate. ")
    else:
        col1, col2 = st.columns(2)
        with col1: 
            affirmative_coaches = st.multiselect("Affirmative coaches", options=coaches, 
                                                placeholder="Select at least 1 coach", 
                                                format_func=lambda t: t["teacher_name"])
            remaining_coaches = [t for t in coaches if t not in affirmative_coaches]
        with col2:
            negative_coaches = st.multiselect("Negative coaches", options=remaining_coaches, 
                                            placeholder="Please select at least one coach", 
                                            format_func=lambda t: t["teacher_name"])
        if affirmative_coaches and negative_coaches:
            return affirmative_coaches, negative_coaches
          
      
def debate_assemble(team_id, motions_sheet, student_pool_sheet, teachers_sheet, squads_sheet):
    motion_id = select_motion(team_id, motions_sheet)
    student_selection = select_students(team_id, student_pool_sheet)
    coach_selection = select_coaches(team_id, teachers_sheet)
    
    if motion_id and student_selection and coach_selection:
        affirmative_speakers, negative_speakers = student_selection
        affirmative_coaches, negative_coaches = coach_selection
        affirmative_speaker_emails = [s["student_email"] for s in affirmative_speakers]
        affirmative_speaker_emails = "; ".join(affirmative_speaker_emails)
        negative_speaker_emails = [s["student_email"] for s in negative_speakers]
        negative_speaker_emails = "; ".join(negative_speaker_emails)
        affirmative_coaches_emails = [t["teacher_email"] for t in affirmative_coaches]
        affirmative_coaches_emails = "; ".join(affirmative_coaches_emails)
        negative_coaches_emails = [t["teacher_email"] for t in negative_coaches]
        negative_coaches_emails = "; ".join(negative_coaches_emails)
        if st.button("Build debate"):
            squads_sheet.append_row([team_id, motion_id, "affirmative", affirmative_coaches_emails, affirmative_speaker_emails, ""])
            squads_sheet.append_row([team_id, motion_id, "negative", negative_coaches_emails, negative_speaker_emails, ""])
            st.success("Debate built successfully. ")    
        
    else:
        st.info("Please complete motion, speaker, and coach selection above.")

    
    

