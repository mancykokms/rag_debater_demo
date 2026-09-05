from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage
import httpx
import streamlit as st

@tool
def web_search(query: str) -> str:
    """Search the web for real, current information on a topic."""
    from rag.web_search import web_search as do_search
    results = do_search(query)
    return "\n\n".join([f"{r['title']} ({r['url']}): {r['content']}" for r in results])

custom_client = httpx.Client(verify=True)

llm = ChatOpenAI(
    model="sensenova-6.8-flash-lite",
    base_url="https://token.sensenova.cn/v1",
    api_key=st.secrets["sensenova"]["api_key"],
    max_tokens=1500,
    extra_body={"reasoning_effort": "none"},
    http_client=custom_client,
)

llm_with_tools = llm.bind_tools([web_search])

messages = [HumanMessage(content="Search for real statistics about esports in schools, then summarize what you find with sources.")]

while True:
    response = llm_with_tools.invoke(messages)
    messages.append(response)
    
    if not response.tool_calls:
        break  # model is done, this is the final answer
    
    for tool_call in response.tool_calls:
        result = web_search.invoke(tool_call["args"])
        messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))

print(response.content)