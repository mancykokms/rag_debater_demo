from crewai import Agent, Task, Crew, LLM
import streamlit as st
from llm.debater import build_system_prompt
from llm.judge import build_judge_prompt
import json
import asyncio


def get_llm(max_tokens=8000):
    llm = LLM(
       model="openai/sensenova-6.7-flash-lite",
       base_url="https://token.sensenova.cn/v1",
       api_key=st.secrets["sensenova"]["api_key"],
       max_tokens=max_tokens,
       reasoning_effort="none",
       )
    return llm 


# async def run_debater_crew(speech_so_far, retrieved_chunks, team_line, speaker_role, stance, mode):
    
#     llm = get_llm()
#     agent = Agent(
#         role="Debater",
#         goal="Help your team to win the debate",
#         backstory=build_system_prompt(speaker_role, stance, mode),
#         llm=llm
#     )
#     evidence = "\n\n".join(retrieved_chunks)
#     if speech_so_far:
#             round_context = f"Full round so far:\n{speech_so_far}"
#     else:
#         round_context = "This is the opening speech of the round — nothing has been said yet."
#     task = Task(
#         description=f"Your team's case line:\n{team_line}\n\nEvidence:\n{evidence}\n\n{round_context}\n\nGenerate your speech as the next speaker in the round.",
#         expected_output="A debate speech responding to the round so far",
#         agent=agent
#     )
#     crew = Crew(agents=[agent], tasks=[task])
#     result = await crew.kickoff_async()
#     return result

async def run_arguments_crew(retrieved_chunks, team_line, speaker_role, stance, mode, need_rebuttals=True):
    llm = get_llm()
    agent = Agent(
        role="Debater", 
        goal="Help your team to win the debate",
        backstory=build_system_prompt(speaker_role, stance, mode),
        llm=llm
    )
    evidence = "\n\n".join(retrieved_chunks)
    if need_rebuttals:
        rebuttal_instruction = "Include a natural transition and the exact placeholder text {rebuttals} at the point where your rebuttal to the opposing side belongs — do not write the rebuttal itself."
    else:
        rebuttal_instruction = "Do not include any rebuttals in your speech. This is the opening speech of the round."
    task = Task(
        description=f"Your team's case line:\n{team_line}\n\nEvidence:\n{evidence}\n\nWrite your opening greeting and constructive arguments. {rebuttal_instruction}",
        expected_output="A complete speech opening (greeting + arguments), including the literal {rebuttals} placeholder if instructed",
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task])
    result = await crew.kickoff_async()
    return result

async def run_rebuttals_crew(speech_so_far, retrieved_chunks, team_line, speaker_role, stance, mode):
    llm = get_llm()
    agent = Agent(
        role="Debater", 
        goal="Help your team to win the debate",
        backstory=build_system_prompt(speaker_role, stance, mode),
        llm=llm
    )
    evidence = "\n\n".join(retrieved_chunks)
    task = Task(
        description=f"Your team's case line:\n{team_line}\n\nEvidence:\n{evidence}\n\nFull round so far:\n{speech_so_far}\n\nGenerate your rebuttals for the debate.",
        expected_output="Rebuttals responding to the arguments made in the round so far, no new arguments, this is to be inserted into a constructed debate speech",
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task])
    result = await crew.kickoff_async()
    return result



async def run_judge_crew(student_speech, speaker_role, stance, team_line, retrieved_chunks):
    llm = get_llm()
    agent = Agent(
            role="Judge",
            goal="Be an unbiased judge to this debate and judge the student's performance",
            backstory=build_judge_prompt(speaker_role, stance),
            llm=llm
        )
    evidence = "\n\n".join(retrieved_chunks)
    task = Task(
        description=f"The team's case line:\n{team_line}\n\nEvidence:\n{evidence}\n\nStudent's speech to judge:\n{student_speech}",
        expected_output=(
            "Valid JSON only, matching exactly this structure: "
            '{"role_specific_score": {...}, "unaddressed_points": [...], '
            '"fallacies_or_gaps": [...], "strengths": [...], "summary_feedback": "..."}'
        ),
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task])
    result = await crew.kickoff_async()
    raw_text = result.raw
    try:
        parsed = json.loads(raw_text)
        return parsed
    except Exception as e:
        return {"error": "Could not parse judge response", "raw_text": raw_text}

if __name__ == "__main__":
    from rag.retrieve import retrieve_relevant_chunks
    
    student_speech = "We believe carbon taxes are necessary because they create a direct financial incentive to reduce emissions."
    results = retrieve_relevant_chunks(query_text=student_speech, team_id="test_team", motion_id="test_motion", n_results=3)
    chunks = results["documents"][0]
    
    feedback = asyncio.run(run_judge_crew(
        student_speech=student_speech,
        speaker_role=1,
        stance="affirmative",
        team_line="We support carbon taxes because they create market incentives that drive innovation and emissions reduction.",
        retrieved_chunks=chunks
    ))
    print(feedback)