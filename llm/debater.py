from openai import OpenAI
import streamlit as st

client = OpenAI(
    base_url="https://token.sensenova.cn/v1",
    api_key=st.secrets["sensenova"]["api_key"],
)

ROLE_STANCE_INSTRUCTIONS = {
    (1, "affirmative"): (
        "You are the 1st Affirmative speaker. Define the motion clearly, "
        "establish your team's burden of proof, and present 2-3 main "
        "contentions with supporting reasoning. This is a constructive "
        "speech — build your case, do not rebut anything yet."
    ),
    (1, "negative"): (
        "You are the 1st Negative speaker. Respond to the Affirmative's "
        "definition (challenge it only if genuinely unreasonable), then "
        "present your own team's counter-case with 2-3 main contentions. "
        "Briefly address the Affirmative's framing, but focus mainly on "
        "building your own constructive case."
    ),
    (2, "affirmative"): (
        "You are the 2nd Affirmative speaker. Rebut the Negative's "
        "contentions directly and specifically. Then extend your own "
        "team's case with new reasoning or evidence — do not simply "
        "repeat the 1st speaker's points."
    ),
    (2, "negative"): (
        "You are the 2nd Negative speaker. Rebut the Affirmative's "
        "contentions directly and specifically. Then extend your own "
        "team's case with new reasoning or evidence — do not simply "
        "repeat the 1st speaker's points."
    ),
    (3, "affirmative"): (
        "You are the 3rd Affirmative speaker. Do NOT introduce any new "
        "arguments or evidence. Focus entirely on rebuttal and weighing — "
        "explain why your side has won the key clashes of the round, "
        "referencing what was actually said by both teams."
    ),
    (3, "negative"): (
        "You are the 3rd Negative speaker. Do NOT introduce any new "
        "arguments or evidence. Focus entirely on rebuttal and weighing — "
        "explain why your side has won the key clashes of the round, "
        "referencing what was actually said by both teams."
    ),
}

MODE_INSTRUCTIONS = {
    "teammate": (
        "You are speaking on the same team as the previous speaker(s). "
        "Stay fully consistent with your team's case line — do not "
        "contradict or repeat what's already been argued. Do not rebut "
        "your own team."
    ),
    "opponent": (
        "You are debating against the student. Use the provided evidence "
        "to genuinely challenge their argument. Do not be agreeable or "
        "validate weak points — push back the way a real opponent would, "
        "while remaining respectful and focused on the substance."
    ),
}


def build_system_prompt(speaker_role, stance, mode):
    role = (speaker_role, stance)
    instructions = ROLE_STANCE_INSTRUCTIONS[role]
    instruction_mode = MODE_INSTRUCTIONS[mode]
    system_prompt = instructions + "\n" + instruction_mode
    return system_prompt
    
    
    
def generate_debater_response(student_speech, retrieved_chunks, team_line, speaker_role, stance, mode):
    system_prompt = build_system_prompt(speaker_role, stance, mode)
    evidence = "\n\n".join(retrieved_chunks)
    user_message = f"Your team's case line:\n{team_line}\n\nEvidence:\n{evidence}\n\nStudent's speech to respond to:\n{student_speech}"
    
    response = client.chat.completions.create(
        model="sensenova-6.7-flash-lite",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
    )
    return response.choices[0].message.content




if __name__ == "__main__":
    from rag.retrieve import retrieve_relevant_chunks
    
    student_speech = "We believe carbon taxes are necessary because they create a direct financial incentive to reduce emissions."
    
    results = retrieve_relevant_chunks(
        query_text=student_speech,
        team_id="test_team",
        motion_id="test_motion",
        n_results=3
    )
    chunks = results["documents"][0]  # remember the extra nesting from .query()
    
    response = generate_debater_response(
        student_speech=student_speech,
        retrieved_chunks=chunks,
        team_line="We oppose carbon taxes because they disproportionately burden low-income households without guaranteeing meaningful emissions reductions.",
        speaker_role=2,
        stance="negative",
        mode="opponent"
    )
    print(response)