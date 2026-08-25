from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import streamlit as st
from pydantic import BaseModel
from typing import Dict, List
from llm.debater import build_system_prompt, ROLE_LABELS, ROLE_STANCE_INSTRUCTIONS, MODE_INSTRUCTIONS
import asyncio

provider = OpenAIProvider(
    base_url="https://token.sensenova.cn/v1",
    api_key=st.secrets["sensenova"]["api_key"],
)

model = OpenAIChatModel("sensenova-6.7-flash-lite", provider=provider)



class JudgeFeedback(BaseModel):
    role_specific_score: Dict[str, int]
    unaddressed_points: List[str]
    fallacies_or_gaps: List[str]
    strengths: List[str]
    summary_feedback: str
    
    
class DebaterResponse(BaseModel):
    speech_text: str
    sources_cited: List[str]

    
judge_agent = Agent(model, output_type=JudgeFeedback)   
debater_agent = Agent(model, output_type=DebaterResponse)

@judge_agent.tool_plain
@debater_agent.tool_plain
def web_search(query: str) -> str:
    """Search the web for real, current information on a topic."""
    from rag.web_search import web_search as do_search
    results = do_search(query)
    return "\n\n".join([f"{r['title']} ({r['url']}): {r['content']}" for r in results])

async def generate_debater_response(student_speech, team_line, speaker_role, stance, mode):
    system_prompt = build_system_prompt(speaker_role, stance, mode)
    
    user_message = f"Your team's case line \n{team_line}\n search the web for real and current evidence to respond to: \n{student_speech}. "
    response = await debater_agent.run(user_message, instructions=system_prompt)
    return response.output
    
    
if __name__ == "__main__":
    result = asyncio.run(generate_debater_response(
        student_speech="We believe carbon taxes are necessary because they create a direct financial incentive to reduce emissions.",
        team_line="We oppose carbon taxes because they disproportionately burden low-income households without guaranteeing meaningful emissions reductions.",
        speaker_role=2,
        stance="negative",
        mode="opponent"
    ))
    print("Speech:", result.speech_text)
    print("Sources:", result.sources_cited)