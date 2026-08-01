# crew/mode3_crew.py
from crew.agents import run_debater_crew, run_judge_crew
from llm.debater import format_transcript, generate_team_line
from rag.retrieve import retrieve_relevant_chunks
from llm.debater import ROLE_LABELS
import streamlit as st
FULL_ROUND_SEQUENCE = [
    (1, "affirmative"), 
    (1, "negative"),
    (2, "affirmative"),
    (2, "negative"),
    (3, "affirmative"),
    (3, "negative")
]
def get_mode_and_team_line(stance, student_stance, team_lines):
    mode = "teammate" if stance == student_stance else "opponent"
    team_line = team_lines.get(stance)
    return mode, team_line
    

def generate_before_context(student_stance, student_role, team_lines):
    student_role = (student_role, student_stance)
    student_idx = FULL_ROUND_SEQUENCE.index(student_role)
    
    speeches = []
    transcript_so_far = ""
    
    for (role, stance) in FULL_ROUND_SEQUENCE[:student_idx]:
        mode, team_line = get_mode_and_team_line(stance, student_stance, team_lines)
        query_text = transcript_so_far if transcript_so_far else team_line
        results = retrieve_relevant_chunks(query_text=query_text, team_id="test_team", motion_id="test_motion", n_results=3)
        chunks = results["documents"][0]
       
        response = run_debater_crew(
            speech_so_far=transcript_so_far,   # was: student_speech=transcript_so_far
            retrieved_chunks=chunks,
            team_line=team_line,
            speaker_role=role,
            stance=stance,
            mode=mode
        )
        speech = {"stance": stance, "speaker_role": role, "text": response.raw}
        speeches.append(speech)
        transcript_so_far = format_transcript(speeches)
        yield speech

def generate_after_context(student_stance, student_role, student_speech, team_lines, previous_speeches):
    student_role = (student_role, student_stance)
    student_idx = FULL_ROUND_SEQUENCE.index(student_role)
    
    student_entry = [{"stance": student_stance, "speaker_role": student_role[0], "text": student_speech}]
    speeches = previous_speeches + student_entry
    transcript_so_far = format_transcript(speeches)
    
    for (role, stance) in FULL_ROUND_SEQUENCE[student_idx + 1:]:
        mode, team_line = get_mode_and_team_line(stance, student_stance, team_lines)
        query_text = transcript_so_far 
        results = retrieve_relevant_chunks(query_text=query_text, team_id="test_team", motion_id="test_motion", n_results=3)
        chunks = results["documents"][0]
       
        response = run_debater_crew(
                    speech_so_far=transcript_so_far,
                    retrieved_chunks=chunks,
                    team_line=team_line,
                    speaker_role=role,
                    stance=stance,
                    mode=mode
                )
        speech = {"stance": stance, "speaker_role": role, "text": response.raw}
        speeches.append(speech)
        transcript_so_far = format_transcript(speeches)
        yield speech
        
# def get_chat_role(stance, student_stance):
#     return "user" if stance == student_stance else "assistant"
        
def render_mode_3(student_stance, student_role, team_lines):
    before_speeches = []
    for speech in generate_before_context(student_stance=student_stance, student_role=student_role, team_lines=team_lines):
        avatar = "🥷" if speech["stance"] != student_stance else "🧑‍🎓"
        st.chat_message(ROLE_LABELS[(speech["speaker_role"], speech["stance"])], avatar=avatar).write(speech["text"])
        before_speeches.append(speech)


    # for speech in before_speeches:
    #     avatar = "🥷" if speech["stance"] != student_stance else "🧑‍🎓"
    #     st.chat_message(ROLE_LABELS[(speech["speaker_role"], speech["stance"])], avatar=avatar).write(speech["text"])
        
    student_speech = st.chat_input("Write your speech")
    if student_speech:
        st.chat_message(ROLE_LABELS[(student_role, student_stance)], avatar="👤").write(student_speech)
        
        results = retrieve_relevant_chunks(
                query_text=student_speech,
                team_id="test_team",
                motion_id="test_motion",
                n_results=3
            )
        chunks = results["documents"][0]
        
        # after_speeches = list(generate_after_context(
        #     student_stance=student_stance,
        #     student_role=student_role,
        #     student_speech=student_speech,
        #     team_lines=team_lines,
        #     previous_speeches=before_speeches
        # ))
        
        # for speech in after_speeches:
        #     avatar = "🥷" if speech["stance"] != student_stance else "🧑‍🎓"
        #     st.chat_message(ROLE_LABELS[(speech["speaker_role"], speech["stance"])], avatar=avatar).write(speech["text"])
        
        after_speeches = []
        for speech in generate_after_context(
            student_stance=student_stance,
            student_role=student_role,
            student_speech=student_speech,
            team_lines=team_lines,
            previous_speeches=before_speeches
        ):
            avatar = "🥷" if speech["stance"] != student_stance else "🧑‍🎓"
            st.chat_message(ROLE_LABELS[(speech["speaker_role"], speech["stance"])], avatar=avatar).write(speech["text"])
            after_speeches.append(speech)
            
        feedback = run_judge_crew(
                    student_speech=student_speech,
                    speaker_role=student_role,
                    stance=student_stance,
                    team_line=team_lines.get(student_stance),
                    retrieved_chunks=chunks
                )
            
        with st.chat_message("judge", avatar="🧑‍⚖️"):
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
            
            
        
            
    
    
        
        

# if __name__ == "__main__":
#     team_lines = {
#         "affirmative": "We support banning single-use plastics because they cause irreversible environmental harm.",
#         "negative": "We oppose banning single-use plastics because it burdens low-income households."
#     }
    
#     for speech in generate_before_context(student_stance="negative", student_role=2, team_lines=team_lines):
#         print(f"{speech['stance']} {speech['speaker_role']}: {speech['text'][:100]}...")

if __name__ == "__main__":
    team_lines = {
        "affirmative": "We support banning single-use plastics because they cause irreversible environmental harm.",
        "negative": "We oppose banning single-use plastics because it burdens low-income households."
    }
    
    before_speeches = list(generate_before_context(student_stance="negative", student_role=2, team_lines=team_lines))
    
    student_speech = "We believe the ban is necessary because plastic pollution is an urgent environmental crisis."
    
    for speech in generate_after_context(
        student_stance="negative",
        student_role=2,
        student_speech=student_speech,
        team_lines=team_lines,
        previous_speeches=before_speeches
    ):
        print(f"{speech['stance']} {speech['speaker_role']}: {speech['text'][:100]}...")