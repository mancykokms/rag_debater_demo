from openai import OpenAI
import streamlit as st
import json

client = OpenAI(
    base_url="https://token.sensenova.cn/v1",
    api_key=st.secrets["sensenova"]["api_key"],
)

JUDGE_ROLE_CRITERIA = {
    (1, "affirmative"): (
        "As 1st Affirmative, judge on: clarity of the motion's definition, "
        "how well they established their team's burden of proof, and the "
        "strength/organization of their main contentions."
    ),
    (1, "negative"): (
        "As 1st Negative, judge on: whether they reasonably engaged with "
        "the Affirmative's definition/framing (not just ignoring it), and "
        "the strength/organization of their own team's counter-case."
    ),
    (2, "affirmative"): (
        "As 2nd Affirmative, judge on: how directly and specifically they "
        "rebutted the Negative's actual points (not straw-manning), and "
        "whether they meaningfully extended their own team's case rather "
        "than just repeating the 1st speaker."
    ),
    (2, "negative"): (
        "As 2nd Negative, judge on: how directly and specifically they "
        "rebutted the Affirmative's actual points (not straw-manning), and "
        "whether they meaningfully extended their own team's case rather "
        "than just repeating the 1st speaker."
    ),
    (3, "affirmative"): (
        "As 3rd Affirmative, judge on: whether they avoided introducing "
        "any new arguments (a real rule violation if they did — flag this "
        "explicitly), and the quality of their rebuttal and weighing of "
        "the round overall."
    ),
    (3, "negative"): (
        "As 3rd Negative, judge on: whether they avoided introducing any "
        "new arguments (a real rule violation if they did — flag this "
        "explicitly), and the quality of their rebuttal and weighing of "
        "the round overall."
    ),
}

JUDGE_SYSTEM_PROMPT_TEMPLATE = """You are an experienced, impartial debate judge evaluating a junior high 3v3 debate speech.

{role_criteria}

In addition to role-specific criteria, evaluate:
- Consistency: did the speaker stay true to their own team's case line (provided below), or did they contradict/drift from it?
- Evidence engagement: given the available evidence provided below, did the speaker address the strongest points, or leave significant evidence unaddressed? List specific unaddressed points if any exist.
- Fallacies or logical gaps: identify any genuine issues (e.g., strawmanning, unsupported claims, circular reasoning) — do not invent problems if the speech is genuinely solid.

Be honest and specific, not just encouraging — a real judge gives actionable, sometimes critical feedback. Do not be harsh for its own sake, but do not inflate a weak speech either.

Respond with ONLY valid JSON, no preamble, no markdown code fences, matching exactly this structure:
{{
  "role_specific_score": {{"clarity": 0-10, "evidence_use": 0-10, "engagement_with_opponent": 0-10}},
  "unaddressed_points": ["...", "..."],
  "fallacies_or_gaps": ["..."],
  "strengths": ["..."],
  "summary_feedback": "2-3 sentences, direct and specific"
}}"""

def build_judge_prompt(speaker_role, stance):
    student = (speaker_role, stance)
    role_criteria = JUDGE_ROLE_CRITERIA[student]
    return JUDGE_SYSTEM_PROMPT_TEMPLATE.format(role_criteria=role_criteria)

def generate_judge_response(student_speech, speaker_role, stance, team_line, retrieved_chunks):
    system_prompt = build_judge_prompt(speaker_role, stance)
    evidence = "\n\n".join(retrieved_chunks)
    user_message = f"The team's case line:\n{team_line}\n\nEvidence:\n{evidence}\n\nStudent's speech to judge:\n{student_speech}"
    response = client.chat.completions.create(
            model="sensenova-6.7-flash-lite",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
        )
    raw_text = response.choices[0].message.content
    try:
        parsed = json.loads(raw_text)
        return parsed
    except Exception as e:
        return {"error": "Could not parse judge response", "raw_text": raw_text}
    
    
if __name__ == "__main__":
    from rag.retrieve import retrieve_relevant_chunks
    
    student_speech = "We believe carbon taxes are necessary because they create a direct financial incentive to reduce emissions."
    
    results = retrieve_relevant_chunks(
        query_text=student_speech,
        team_id="test_team",
        motion_id="test_motion",
        n_results=3
    )
    chunks = results["documents"][0]
    
    feedback = generate_judge_response(
        student_speech=student_speech,
        speaker_role=1,
        stance="affirmative",
        team_line="We support carbon taxes because they create market incentives that drive innovation and emissions reduction.",
        retrieved_chunks=chunks
    )
    print(feedback)
    