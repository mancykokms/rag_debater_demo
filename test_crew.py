from crewai import Agent, Task, Crew, LLM
import streamlit as st
from llm.debater import build_system_prompt, generate_debater_response
from llm.judge import build_judge_prompt, generate_judge_response
import json
# llm = LLM(
#     model="sensenova-6.7-flash-lite",
#     base_url="https://token.sensenova.cn/v1",
#     api_key=st.secrets["sensenova"]["api_key"],
# )

# test_agent = Agent(
#     role="Greeter",
#     goal="Say hello in a friendly way",
#     backstory="You are a warm, welcoming assistant.",
#     llm=llm
# )

# test_task = Task(
#     description="Say hello and introduce yourself in one sentence.",
#     expected_output="A one-sentence friendly greeting.",
#     agent=test_agent
# )

# crew = Crew(agents=[test_agent], tasks=[test_task])
# result = crew.kickoff()
# print(result)



def run_debater_crew(student_speech, retrieved_chunks, team_line, speaker_role, stance, mode):
    llm = LLM(
    model="sensenova-6.7-flash-lite",
    base_url="https://token.sensenova.cn/v1",
    api_key=st.secrets["sensenova"]["api_key"],
    )
    agent = Agent(
        role="Debater",
        goal="Help your team to win the debate",
        backstory=build_system_prompt(speaker_role, stance, mode),
        llm=llm
    )
    evidence = "\n\n".join(retrieved_chunks)
    task = Task(
        description=f"Your team's case line:\n{team_line}\n\nEvidence:\n{evidence}\n\nStudent's speech to respond to:\n{student_speech}",
        expected_output="A debate speech responding to the opponent",
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task])
    result = crew.kickoff()
    return result

def run_judge_crew(student_speech, speaker_role, stance, team_line, retrieved_chunks):
    llm = LLM(
        model="sensenova-6.7-flash-lite",
        base_url="https://token.sensenova.cn/v1",
        api_key=st.secrets["sensenova"]["api_key"],
        )
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
    result = crew.kickoff()
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
    
    feedback = run_judge_crew(
        student_speech=student_speech,
        speaker_role=1,
        stance="affirmative",
        team_line="We support carbon taxes because they create market incentives that drive innovation and emissions reduction.",
        retrieved_chunks=chunks
    )
    print(feedback)