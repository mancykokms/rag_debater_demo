from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import streamlit as st
from pydantic import BaseModel
from typing import Dict, List

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
    
judge_agent = Agent(model, output_type=JudgeFeedback)   
 

@Agent.tool_plain
def web_search(query: str) -> str:
    """Search the web for real, current information on a topic."""
    from rag.web_search import web_search as do_search
    results = do_search(query)
    return "\n\n".join([f"{r['title']} ({r['url']}): {r['content']}" for r in results])