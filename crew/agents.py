from crewai import Agent, Task, Crew, LLM
import streamlit as st
from llm.debater import build_system_prompt
from llm.judge import build_judge_prompt
import json
import asyncio
from crewai.tools import tool


ARGUMENT_WORD_LIMITS = {1: 350, 2: 150, 3: 200}

ARGUMENT_CHECKLISTS = {
    (1, "affirmative"): "It MUST include, even briefly: (1) a clear definition of the motion, (2) your team's burden of proof, and (3) 2-3 distinct contentions each with a reason.",
    (1, "negative"): "It MUST include, even briefly: (1) brief acceptance of (or challenge to, only if genuinely unreasonable) the Affirmative's definition, and (2) 2-3 distinct contentions for your own counter-case, each with a reason. Do NOT redefine the motion from scratch.",
    (2, "affirmative"): "It MUST include, even briefly: 1-2 new points extending your team's case beyond what's already been said — do not just repeat the 1st speaker.",
    (2, "negative"): "It MUST include, even briefly: 1-2 new points extending your team's case beyond what's already been said — do not just repeat the 1st speaker.",
    (3, "affirmative"): "It MUST include, even briefly: a clear weighing of the round so far — which clashes your side is winning and why. Do NOT introduce any new arguments.",
    (3, "negative"): "It MUST include, even briefly: a clear weighing of the round so far — which clashes your side is winning and why. Do NOT introduce any new arguments.",
}


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
#     result = await crew.akickoff()
#     return result

@tool("web_search")
def web_search_tool(query: str) -> str:
    """Search the web for real, current information on a topic"""
    from rag.web_search import web_search
    results = web_search(query)
    return "\n\n".join([f"{r["title"]} ({r["url"]}): {r["content"]}" for r in results])

async def run_arguments_crew(team_line, speaker_role, stance, mode, need_rebuttals=True):
    word_limit = ARGUMENT_WORD_LIMITS[speaker_role]
    checklist = ARGUMENT_CHECKLISTS[(speaker_role, stance)]
    llm = get_llm()
    agent = Agent(
        role="Debater", 
        goal="Help your team to win the debate using real, current evidence from web search",
        backstory=build_system_prompt(speaker_role, stance, mode),
        llm=llm, 
        tools=[web_search_tool]
    )
    
    if need_rebuttals:
        rebuttal_instruction = "Include a natural transition and the exact placeholder text {rebuttals} at the point where your rebuttal to the opposing side belongs — do not write the rebuttal itself."
    else:
        rebuttal_instruction = "Do not include any rebuttals in your speech. This is the opening speech of the round."
    task = Task(
        description=(
            f"Your team's case line:\n{team_line}\n\n"
            f"Search the web for real, current evidence to support this case line before writing. "
            f"Write your debate speech in under {word_limit} words. "
            f"{checklist} Cite your sources naturally within the speech. Be concise in each part rather than dropping any of them. "
            f"{rebuttal_instruction}"
        ),
        expected_output=f"A complete speech opening (greeting + arguments), including the literal {{rebuttals}} placeholder if instructed, keep it under {word_limit}",
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task])
    result = await crew.akickoff()
    return result

REBUTTAL_WORD_LIMITS = {1: 150, 2: 200, 3: 350}

REBUTTAL_CHECKLISTS = {
    1: "Briefly respond to the Affirmative's definition and opening case (challenge the definition only if genuinely unreasonable) — keep this part short, since your main job is building your own case, not rebutting yet.",
    2: "Directly engage with 1-2 specific points from the opposing side's most recent speech — quote or clearly reference what they actually said, don't argue generically.",
    3: "Directly engage with the key clashes of the round so far, and weigh which side is winning. Do NOT introduce any new arguments or evidence.",
}


async def run_rebuttals_crew(speech_so_far, team_line, speaker_role, stance, mode):
    llm = get_llm()
    word_limit = REBUTTAL_WORD_LIMITS[speaker_role]
    rebuttal_checklist = REBUTTAL_CHECKLISTS[speaker_role]
    
    agent = Agent(
        role="Debater", 
        goal="Help your team to win the debate",
        backstory=build_system_prompt(speaker_role, stance, mode),
        llm=llm, 
        tools=[web_search_tool]
    )

    task = Task(
        # description=f"Your team's case line:\n{team_line}\n\nFull round so far:\n{speech_so_far}\n\nGenerate your rebuttal in under {word_limit} words. {rebuttal_checklist}",
        description=(
            f"Your team's case line:\n{team_line}\n\n"
            f"Full round so far:\n{speech_so_far}\n\n"
            f"Search the web for real, current evidence to respond to your opponents and support this case line before writing. "
            f"Write your rebuttals in under {word_limit} words. "
            f"Do not include any greetings or closings. "
            f"{rebuttal_checklist} Cite your sources naturally within each rebuttals. Be concise in each part rather than dropping any of them. "
        ),
        expected_output=f"Rebuttals responding to the arguments made in the round so far, no new arguments, no greetings, grounded in real cited evidence, under {word_limit} words",
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task])
    result = await crew.akickoff()
    return result



async def run_judge_crew(student_speech, speaker_role, stance, team_line):
    llm = get_llm()
    agent = Agent(
            role="Judge",
            goal="Be an unbiased judge to this debate and judge the student's performance",
            backstory=build_judge_prompt(speaker_role, stance),
            llm=llm, 
            tools=[web_search_tool]
        )

    task = Task(
        # description=f"The team's case line:\n{team_line}\n\nSearch for real, current evidence. \n\nStudent's speech to judge:\n{student_speech}",
        description=(
            f"The team's case line: \n{team_line}\n\n"
            f"Search the web for real, current evidence and strong arguments relevant to this motion, "
            f"to identify what points, evidence, or rebuttals a string speech should have addressed. \n\n"
            f"Student's speech to judge: {student_speech}\n\n"
            f"Using what you find, evaluate the speech - specifically flag in unaddressed_points any "
            f"significant real evidence or arguments the student did not engage with. "
        ),
        expected_output=(
            "Valid JSON only, matching exactly this structure: "
            '{"role_specific_score": {...}, "unaddressed_points": [...], '
            '"fallacies_or_gaps": [...], "strengths": [...], "summary_feedback": "..."}'
        ),
        agent=agent
    )
    crew = Crew(agents=[agent], tasks=[task])
    result = await crew.akickoff()
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