from email.mime import text

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
        "speech — build your case, do not rebut anything yet. "
        "Keep your speech in under 500 words. "
    ),
    (1, "negative"): (
        "You are the 1st Negative speaker. Respond to the Affirmative's "
        "definition (challenge it only if genuinely unreasonable), then "
        "present your own team's counter-case with 2-3 main contentions. "
        "Briefly address the Affirmative's framing, but focus mainly on "
        "building your own constructive case. "
        "Keep your speech in under 500 words. "
    ),
    (2, "affirmative"): (
        "You are the 2nd Affirmative speaker. Rebut the Negative's "
        "contentions directly and specifically. Then extend your own "
        "team's case with new reasoning or evidence — do not simply "
        "repeat the 1st speaker's points. "
        "Keep your speech in under 500 words. "
    ),
    (2, "negative"): (
        "You are the 2nd Negative speaker. Rebut the Affirmative's "
        "contentions directly and specifically. Then extend your own "
        "team's case with new reasoning or evidence — do not simply "
        "repeat the 1st speaker's points. "
        "Keep your speech in under 500 words. "
    ),
    (3, "affirmative"): (
        "You are the 3rd Affirmative speaker. Do NOT introduce any new "
        "arguments or evidence. Focus entirely on rebuttal and weighing — "
        "explain why your side has won the key clashes of the round, "
        "referencing what was actually said by both teams. "
        "Keep your speech in under 500 words. "
    ),
    (3, "negative"): (
        "You are the 3rd Negative speaker. Do NOT introduce any new "
        "arguments or evidence. Focus entirely on rebuttal and weighing — "
        "explain why your side has won the key clashes of the round, "
        "referencing what was actually said by both teams. "
        "Keep your speech in under 500 words. "
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

ROLE_LABELS = {
    (1, "affirmative"): "Affirmative 1st Speaker",
    (1, "negative"): "Negative 1st Speaker",
    (2, "affirmative"): "Affirmative 2nd Speaker",
    (2, "negative"): "Negative 2nd Speaker",
    (3, "affirmative"): "Affirmative 3rd Speaker",
    (3, "negative"): "Negative 3rd Speaker",
}

def build_system_prompt(speaker_role, stance, mode):
    role = (speaker_role, stance)
    instructions = ROLE_STANCE_INSTRUCTIONS[role]
    instruction_mode = MODE_INSTRUCTIONS[mode]
    system_prompt = instructions + "\n" + instruction_mode
    return system_prompt

def get_next_speaker(stance, speaker_role):
    if stance == "affirmative":
        return "negative", speaker_role
    else:  # stance == "negative"
        if speaker_role == 3:
            return None  # last speech of the round, nothing follows
        else:
            return "affirmative", speaker_role + 1  

def format_speech(speaker_role, stance, speech_text):
    role_label = ROLE_LABELS[(speaker_role, stance)]
    formatted_speech = f"{role_label}:\n{speech_text}"
    return formatted_speech

def format_transcript(speeches):
    formatted_transcript = []
    for speech in speeches:
        speaker_role = speech["speaker_role"]
        stance = speech["stance"]
        text = speech["text"]
        formatted_transcript.append(format_speech(speaker_role, stance, text))
    return "\n\n".join(formatted_transcript)

def generate_team_line(stance, motion_text):
    response = client.chat.completions.create(
        model="sensenova-6.7-flash-lite",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a debate coach. Generate a concise, clear, and "
                    "persuasive team line for the opposite stance. The team line "
                    "should be 1-2 sentences long and capture the essence of "
                    "the team's position."
                ),
            },
            {"role": "user", "content": f"Motion: {motion_text}\nStance: {stance}\n\nGenerate the case line."},
        ],
    )   
    return response.choices[0].message.content

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
    
    opponent_team_line = generate_team_line(stance="negative", motion_text="The motion is that carbon taxes are necessary.")
    response = generate_debater_response(
        student_speech=student_speech,
        retrieved_chunks=chunks,
        team_line=opponent_team_line,
        speaker_role=2,
        stance="negative",
        mode="opponent"
    )
    print(response)