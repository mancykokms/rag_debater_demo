from crewai import Agent, Task, Crew
from crewai.tools import tool
from crew.agents import get_llm

@tool("web_search")
def web_search_tool(query: str) -> str:
    """Search the web for real, current information on a topic."""
    from rag.web_search import web_search
    results = web_search(query)
    return "\n\n".join([f"{r['title']} ({r['url']}): {r['content']}" for r in results])

llm = get_llm()
agent = Agent(
    role="Researcher",
    goal="Find real evidence to support arguments",
    backstory="You research topics using web search before answering.",
    llm=llm,
    tools=[web_search_tool]
)
task = Task(
    description="Search for real statistics about the benefits of esports in schools, then summarize what you found with sources.",
    expected_output="A summary with cited sources",
    agent=agent
)
crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
print(result.raw)