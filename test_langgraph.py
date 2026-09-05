# # from langgraph.graph import StateGraph, END
# # from langgraph.checkpoint.memory import InMemorySaver
# # from typing import TypedDict

# # class DebateState(TypedDict):
# #     transcript: str

# # def generate_first_speech(state: DebateState) -> DebateState:
# #     return {"transcript": state["transcript"] + "\n[AI speech placeholder]"}

# # graph = StateGraph(DebateState)
# # graph.add_node("first_speech", generate_first_speech)
# # graph.set_entry_point("first_speech")
# # graph.add_edge("first_speech", END)

# # checkpointer = InMemorySaver()
# # app = graph.compile(checkpointer=checkpointer)

# # config = {"configurable": {"thread_id": "test-thread-1"}}
# # result = app.invoke({"transcript": ""}, config=config)
# # print(result)

# from langgraph.graph import StateGraph, END
# from langgraph.checkpoint.memory import InMemorySaver
# from langgraph.types import interrupt, Command
# from typing import TypedDict

# class DebateState(TypedDict):
#     transcript: str

# def generate_first_speech(state: DebateState) -> DebateState:
#     return {"transcript": state["transcript"] + "\n[AI speech placeholder]"}

# def get_student_speech(state: DebateState) -> DebateState:
#     student_input = interrupt("Please provide your speech")
#     return {"transcript": state["transcript"] + f"\n[Student]: {student_input}"}

# graph = StateGraph(DebateState)
# graph.add_node("first_speech", generate_first_speech)
# graph.add_node("student_turn", get_student_speech)
# graph.set_entry_point("first_speech")
# graph.add_edge("first_speech", "student_turn")
# graph.add_edge("student_turn", END)

# checkpointer = InMemorySaver()
# app = graph.compile(checkpointer=checkpointer)

# config = {"configurable": {"thread_id": "test-thread-2"}}

# # First invoke — runs until it hits the interrupt
# result = app.invoke({"transcript": ""}, config=config)
# print("After first invoke:", result)

# # Resume with the "student's" input
# result2 = app.invoke(Command(resume="This is my test speech"), config=config)
# print("After resume:", result2)


from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from typing import TypedDict

class DebateState(TypedDict):
    transcript: str

def generate_first_speech(state: DebateState) -> DebateState:
    return {"transcript": state["transcript"] + "\n[AI speech placeholder]"}

def get_student_speech(state: DebateState) -> DebateState:
    student_input = interrupt("Please provide your speech")
    return {"transcript": state["transcript"] + f"\n[Student]: {student_input}"}

graph = StateGraph(DebateState)
graph.add_node("first_speech", generate_first_speech)
graph.add_node("student_turn", get_student_speech)
graph.set_entry_point("first_speech")
graph.add_edge("first_speech", "student_turn")
graph.add_edge("student_turn", END)

checkpointer = InMemorySaver()
app = graph.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "test-thread-2"}}

# First invoke — runs until it hits the interrupt
result = app.invoke({"transcript": ""}, config=config)
print("After first invoke:", result)

# Resume with the "student's" input
result2 = app.invoke(Command(resume="This is my test speech"), config=config)
print("After resume:", result2)