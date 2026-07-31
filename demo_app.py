import streamlit as st

st.title("AI Debate Sparring Partner — Demo")

# Hardcoded for now — real motion will come from seed data later
motion_text = "This House Would ban single-use plastics"
team_line_affirmative = "We support banning single-use plastics because they cause irreversible environmental harm and viable alternatives exist."
team_line_negative = "We oppose banning single-use plastics because it disproportionately burdens low-income consumers and businesses without adequate alternatives being widely available."

st.subheader(motion_text)

stance = st.selectbox("Pick your stance", options=["affirmative", "negative"])
speaker_role = st.selectbox("Pick your speaker role", options=[1, 2, 3])
team_line = st.text_input("Enter your team line")
student_speech = st.text_area("Write your speech")

if st.button("Submit speech"):
    st.write("Stance:", stance)
    st.write("Role:", speaker_role)
    st.write("Speech:", student_speech)