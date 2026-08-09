# # import time
# # from openai import OpenAI
# # from crewai import Agent, Task, Crew, LLM
# # import streamlit as st

# # test_prompt = "Write a 150-word argument for why school libraries are important."

# # # Raw client test
# # client = OpenAI(base_url="https://token.sensenova.cn/v1", api_key=st.secrets["sensenova"]["api_key"])
# # start = time.time()
# # response = client.chat.completions.create(
# #     model="sensenova-6.7-flash-lite",
# #     messages=[{"role": "user", "content": test_prompt}],
# #     max_tokens=1000,
# #     reasoning_effort="none",
# # )
# # print("RAW CLIENT:", response.usage, f"{time.time()-start:.1f}s")

# # # CrewAI test
# # llm = LLM(model="openai/sensenova-6.7-flash-lite", base_url="https://token.sensenova.cn/v1", api_key=st.secrets["sensenova"]["api_key"], max_tokens=1000, reasoning_effort="none")
# # agent = Agent(role="Writer", goal="Write arguments", backstory="You write concise arguments.", llm=llm)
# # task = Task(description=test_prompt, expected_output="A 150-word argument", agent=agent)
# # crew = Crew(agents=[agent], tasks=[task])
# # start = time.time()
# # result = crew.kickoff()
# # print("CREWAI:", f"{time.time()-start:.1f}s")


# # from openai import OpenAI
# # import streamlit as st

# # client = OpenAI(base_url="https://token.sensenova.cn/v1", api_key=st.secrets["sensenova"]["api_key"])

# # # Test A: simple prompt (like your original working version)
# # simple_prompt = "Write a 150-word argument for why school libraries are important."

# # # Test B: the actual current placeholder-based prompt
# # placeholder_prompt = "Write a 150-word argument for why school libraries are important. Include a natural transition and the exact placeholder text {rebuttals} at the point where a rebuttal would belong — do not write the rebuttal itself."

# # for name, prompt in [("SIMPLE", simple_prompt), ("PLACEHOLDER", placeholder_prompt)]:
# #     response = client.chat.completions.create(
# #         model="sensenova-6.7-flash-lite",
# #         messages=[{"role": "user", "content": prompt}],
# #         max_tokens=2000,
# #         reasoning_effort="none",
# #     )
# #     print(name, response.usage)


# # test_concurrency.py
# import asyncio
# import time
# from crew.agents import run_arguments_crew
# from rag.retrieve import retrieve_relevant_chunks

# results = retrieve_relevant_chunks(query_text="school libraries", team_id="test_team", motion_id="test_motion", n_results=3)
# chunks = results["documents"][0]

# team_line_aff = "We support school libraries because they improve literacy and provide equal access to information."
# team_line_neg = "We oppose expanding school libraries because funds are better spent on direct classroom resources."

# async def main():
#     # Sequential: one at a time
#     start = time.time()
#     r1 = await run_arguments_crew(chunks, team_line_aff, 1, "affirmative", "opponent", need_rebuttals=False)
#     r2 = await run_arguments_crew(chunks, team_line_neg, 1, "negative", "opponent", need_rebuttals=False)
#     print("SEQUENTIAL elapsed:", time.time() - start)
#     print("R1 usage:", getattr(r1, "token_usage", "no token_usage attr"))
#     print("R2 usage:", getattr(r2, "token_usage", "no token_usage attr"))
    
#     print("\n---\n")
    
#     # Concurrent: both at once
#     start = time.time()
#     r3, r4 = await asyncio.gather(
#         run_arguments_crew(chunks, team_line_aff, 1, "affirmative", "opponent", need_rebuttals=False),
#         run_arguments_crew(chunks, team_line_neg, 1, "negative", "opponent", need_rebuttals=False),
#     )
#     print("CONCURRENT elapsed:", time.time() - start)
#     print("R3 usage:", getattr(r3, "token_usage", "no token_usage attr"))
#     print("R4 usage:", getattr(r4, "token_usage", "no token_usage attr"))

# asyncio.run(main())


# from openai import OpenAI
# import streamlit as st

# client = OpenAI(base_url="https://token.sensenova.cn/v1", api_key=st.secrets["sensenova"]["api_key"])

# response = client.chat.completions.create(
#     model="sensenova-6.7-flash-lite",
#     messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
#     tools=[{
#         "type": "function",
#         "function": {
#             "name": "get_weather",
#             "description": "Get current weather for a location",
#             "parameters": {"type": "object", "properties": {"location": {"type": "string"}}, "required": ["location"]}
#         }
#     }]
# )
# print(response.choices[0].message)


from tavily import TavilyClient
import streamlit as st

client = TavilyClient(api_key=st.secrets["tavily"]["api_key"])

results = client.search(query="esports in schools benefits statistics", max_results=3)
print(results)