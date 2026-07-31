import streamlit as st
from rag.retrieve import retrieve_relevant_chunks
from crew.agents import run_debater_crew, run_judge_crew

st.title("AI Debate Sparring Partner — Demo")

# Hardcoded for now — real motion will come from seed data later
motion_text = "This House Would ban single-use plastics"
team_line_affirmative = "We support banning single-use plastics because they cause irreversible environmental harm and viable alternatives exist."
team_line_negative = "We oppose banning single-use plastics because it disproportionately burdens low-income consumers and businesses without adequate alternatives being widely available."

st.subheader(motion_text)

stance = st.selectbox("Pick your stance", options=["affirmative", "negative"])
speaker_role = st.selectbox("Pick your speaker role", options=[1, 2, 3])
team_line = st.text_input("Enter your team line")



def get_next_speaker(stance, speaker_role):
    if stance == "affirmative":
        return "negative", speaker_role
    else:  # stance == "negative"
        if speaker_role == 3:
            return None  # last speech of the round, nothing follows
        else:
            return "affirmative", speaker_role + 1


if "messages" not in st.session_state:
    st.session_state.messages = []
    
for msg in st.session_state.messages:
    st.session_state_messages = []
    
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        
student_speech = st.chat_input("Write your speech")

if student_speech:
    st.session_state.messages.append({"role": "user", "content": student_speech})
    with st.chat_message("user"):
        st.write(student_speech)
        
    results = retrieve_relevant_chunks(
        query_text=student_speech,
        team_id="test_team",
        motion_id="test_motion",
        n_results=3
    )
    chunks = results["documents"][0]
    
    next_speaker = get_next_speaker(stance, speaker_role)
    
    if next_speaker is not None:
        next_speaker_stance, next_speaker_role = next_speaker
        opponent_team_line = team_line_affirmative if next_speaker_stance == "affirmative" else team_line_negative

        opponent_response = run_debater_crew(
            student_speech=student_speech,
            retrieved_chunks=chunks,
            team_line=opponent_team_line,
            speaker_role=next_speaker_role,
            stance=next_speaker_stance,
            mode="opponent"
        )
            
        with st.chat_message("opponent"):
            st.write(opponent_response.raw)
    else:
        st.info("This was the final speech of the round — no more rebuttals.")
        
    
    feedback = run_judge_crew(
            student_speech=student_speech,
            speaker_role=speaker_role,
            stance=stance,
            team_line=team_line,
            retrieved_chunks=chunks
        )
    
    with st.chat_message("judge"):
        st.markdown(f"**Summary:** {feedback['summary_feedback']}")
        st.markdown("**Scores:**")
        for category, score in feedback['role_specific_score'].items():
            st.metric(category.replace('_', ' ').title(), f"{score}/10")
        if feedback.get('unaddressed_points'):
            st.markdown("**Unaddressed points:**")
            for point in feedback['unaddressed_points']:
                st.markdown(f"- {point}")
        

    