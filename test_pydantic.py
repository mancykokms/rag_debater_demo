# import asyncio
# from pydantic_ai import Agent
# from pydantic_ai.models.openai import OpenAIChatModel
# from pydantic_ai.providers.openai import OpenAIProvider
# import streamlit as st

# provider = OpenAIProvider(
#     base_url="https://token.sensenova.cn/v1",
#     api_key=st.secrets["sensenova"]["api_key"],
# )
# model = OpenAIChatModel("sensenova-6.7-flash-lite", provider=provider)
# agent = Agent(model)

# result = asyncio.run(agent.run("Write a 150-word argument for why school libraries are important."))
# print(result.output)
# print(result.usage)

import asyncio
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
import streamlit as st

provider = OpenAIProvider(
    base_url="https://token.sensenova.cn/v1",
    api_key=st.secrets["sensenova"]["api_key"],
)
model = OpenAIChatModel("sensenova-6.7-flash-lite", provider=provider)
agent = Agent(model)

@agent.tool_plain
def web_search(query: str) -> str:
    """Search the web for real, current information on a topic."""
    from rag.web_search import web_search as do_search
    results = do_search(query)
    return "\n\n".join([f"{r['title']} ({r['url']}): {r['content']}" for r in results])

result = asyncio.run(agent.run("Search for real statistics about esports in schools, then summarize what you find with sources."))
print(result.output)
print(result.usage)