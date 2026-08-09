from tavily import TavilyClient
import streamlit as st

def web_search(query, max_results=3):
    client = TavilyClient(api_key=st.secrets["tavily"]["api_key"])
    results = client.search(query=query, max_results=max_results)
    return [
        {"title": r["title"], "url": r["url"], "content": r["content"]}
        for r in results["results"]
    ]
    
    
WEB_SEARCH_TOOL = [{
    "type": "function",
    "function": {
        "name": "web_search", 
        "description": "Search the web for real, current information on a topic.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query"}},
            "required": ["query"]
        }
    }
}]