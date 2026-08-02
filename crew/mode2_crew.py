# crew/mode2_crew.py
import asyncio
import logging
import time

from crew.agents import run_arguments_crew, run_judge_crew, run_rebuttals_crew
from llm.debater import format_transcript, generate_team_line
from rag.retrieve import retrieve_relevant_chunks
from llm.debater import ROLE_LABELS
import streamlit as st

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
FULL_ROUND_SEQUENCE = [
    (1, "affirmative"), 
    (1, "negative"),
    (2, "affirmative"),
    (2, "negative"),
    (3, "affirmative"),
    (3, "negative")
]
def get_mode_and_team_line(stance, student_stance, team_lines):
    mode = "teammate" if stance == student_stance else "opponent"
    team_line = team_lines.get(stance)
    return mode, team_line
    

async def generate_before_context(student_stance, student_role, team_lines, team_id, motion_id):
    student_role = (student_role, student_stance)
    student_idx = FULL_ROUND_SEQUENCE.index(student_role)
    before_student_list = FULL_ROUND_SEQUENCE[:student_idx]
    
    # argument_positions = [(role, stance) for (role, stance) in before_student_list]
    argument_tasks = {
        (role, stance): asyncio.create_task(build_arguments_for(role, stance, student_stance, team_lines, need_rebuttals=not (role == 1 and stance == "affirmative"), team_id=team_id, motion_id=motion_id)) for (role, stance) in before_student_list
    }
    
    speeches = []
    transcript_so_far = ""
    
    for (role, stance) in before_student_list:
        
        
        # build arguments in parallel
        if (role, stance) in argument_tasks:
            argument_response = await argument_tasks[(role, stance)]
            
            
        if not (role == 1 and stance == "affirmative"):
            if "{rebuttals}" in argument_response["text"]:
                combined_text = argument_response["text"].replace("{rebuttals}", await build_rebuttals_for(transcript_so_far, role, stance, student_stance, team_lines, team_id, motion_id))
            else:
                combined_text = argument_response["text"]
        else:
            combined_text = argument_response["text"]
       
        
        speech = {"stance": stance, "speaker_role": role, "text": combined_text}
        speeches.append(speech)
        transcript_so_far = format_transcript(speeches)
        yield speech
        

async def generate_after_context(student_stance, student_role, student_speech, team_lines, previous_speeches, team_id, motion_id):
    student_role = (student_role, student_stance)
    student_idx = FULL_ROUND_SEQUENCE.index(student_role)
    after_student_list = FULL_ROUND_SEQUENCE[student_idx + 1:]
    
    student_entry = [{"stance": student_stance, "speaker_role": student_role[0], "text": student_speech}]
    speeches = previous_speeches + student_entry
    transcript_so_far = format_transcript(speeches)
    argument_tasks = {
            (role, stance): asyncio.create_task(build_arguments_for(role, stance, student_stance, team_lines, need_rebuttals=not (role == 1 and stance == "affirmative"), team_id=team_id, motion_id=motion_id)) for (role, stance) in after_student_list
        }
    
    for (role, stance) in after_student_list:
        if (role, stance) in argument_tasks:
            argument_response = await argument_tasks[(role, stance)]
            
        if not (role == 1 and stance == "affirmative"):
            if "{rebuttals}" in argument_response["text"]:
                rebuttal_text = await build_rebuttals_for(transcript_so_far, role, stance, student_stance, team_lines, team_id, motion_id)
                combined_text = argument_response["text"].replace("{rebuttals}", rebuttal_text)
            else:   
                combined_text = argument_response["text"]
        
        
        
        speech = {"stance": stance, "speaker_role": role, "text": combined_text}
        speeches.append(speech)
        transcript_so_far = format_transcript(speeches)
        yield speech
        
async def build_arguments_for(role, stance, student_stance, team_lines, team_id, motion_id, need_rebuttals=True):
    start = time.perf_counter()
    logger.info("build_arguments_for start role=%s stance=%s", role, stance)
    mode, team_line = get_mode_and_team_line(stance, student_stance, team_lines)
    results = retrieve_relevant_chunks(query_text=team_line, team_id=team_id, motion_id=motion_id, n_results=3)
    chunks = results["documents"][0]
    response = await run_arguments_crew(
        retrieved_chunks=chunks,
        team_line=team_line,
        speaker_role=role,
        stance=stance,
        mode=mode,
        need_rebuttals=need_rebuttals
    )
    elapsed = time.perf_counter() - start
    logger.info("build_arguments_for done role=%s stance=%s elapsed=%.2fs", role, stance, elapsed)
    return {"stance": stance, "speaker_role": role, "text": response.raw}

async def build_rebuttals_for(speech_so_far, role, stance, student_stance, team_lines, team_id, motion_id):
    start = time.perf_counter()
    logger.info("build_rebuttals_for start role=%s stance=%s", role, stance)
    mode, team_line = get_mode_and_team_line(stance, student_stance, team_lines)
    results = retrieve_relevant_chunks(query_text=speech_so_far, team_id=team_id, motion_id=motion_id, n_results=3)
    chunks = results["documents"][0]
    response = await run_rebuttals_crew(
        speech_so_far=speech_so_far,
        retrieved_chunks=chunks,
        team_line=team_line,
        speaker_role=role,
        stance=stance,
        mode=mode
    )
    elapsed = time.perf_counter() - start
    logger.info("build_rebuttals_for done role=%s stance=%s elapsed=%.2fs", role, stance, elapsed)
    return response.raw

async def render_mode_3(student_stance, student_role, team_lines, team_id, motion_id):
    before_speeches = []
    async for speech in generate_before_context(student_stance=student_stance, student_role=student_role, team_lines=team_lines, team_id=team_id, motion_id=motion_id):
        avatar = "🥷" if speech["stance"] != student_stance else "🧑‍🎓"
        st.chat_message(ROLE_LABELS[(speech["speaker_role"], speech["stance"])], avatar=avatar).write(speech["text"])
        before_speeches.append(speech)


    # for speech in before_speeches:
    #     avatar = "🥷" if speech["stance"] != student_stance else "🧑‍🎓"
    #     st.chat_message(ROLE_LABELS[(speech["speaker_role"], speech["stance"])], avatar=avatar).write(speech["text"])
        
    student_speech = st.chat_input("Write your speech")
    if student_speech:
        st.chat_message(ROLE_LABELS[(student_role, student_stance)], avatar="👤").write(student_speech)
        
        results = retrieve_relevant_chunks(
                query_text=student_speech,
                team_id=team_id,
                motion_id=motion_id,
                n_results=3
            )
        chunks = results["documents"][0]
        
        # after_speeches = list(generate_after_context(
        #     student_stance=student_stance,
        #     student_role=student_role,
        #     student_speech=student_speech,
        #     team_lines=team_lines,
        #     previous_speeches=before_speeches
        # ))
        
        # for speech in after_speeches:
        #     avatar = "🥷" if speech["stance"] != student_stance else "🧑‍🎓"
        #     st.chat_message(ROLE_LABELS[(speech["speaker_role"], speech["stance"])], avatar=avatar).write(speech["text"])
        
        after_speeches = []
        async for speech in generate_after_context(
            student_stance=student_stance,
            student_role=student_role,
            student_speech=student_speech,
            team_lines=team_lines,
            previous_speeches=before_speeches,
            team_id=team_id,
            motion_id=motion_id
        ):
            avatar = "🥷" if speech["stance"] != student_stance else "🧑‍🎓"
            st.chat_message(ROLE_LABELS[(speech["speaker_role"], speech["stance"])], avatar=avatar).write(speech["text"])
            after_speeches.append(speech)
            
        feedback = await run_judge_crew(
                    student_speech=student_speech,
                    speaker_role=student_role,
                    stance=student_stance,
                    team_line=team_lines.get(student_stance),
                    retrieved_chunks=chunks
                    )
            
        with st.chat_message("judge", avatar="🧑‍⚖️"):
            st.markdown(f"**Summary:** {feedback['summary_feedback']}")
            st.markdown("**Scores:**")
            score_cols = st.columns(3)
            for i, (category, score) in enumerate(feedback['role_specific_score'].items()):
                with score_cols[i % 3]:
                    st.metric(category.replace('_', ' ').title(), f"{score}/10")
            if feedback.get('unaddressed_points'):
                st.markdown("**Unaddressed points:**")
                for point in feedback['unaddressed_points']:
                    st.markdown(f"- {point}")
            
            
        
            
    
    
        
        

# if __name__ == "__main__":
#     team_lines = {
#         "affirmative": "We support banning single-use plastics because they cause irreversible environmental harm.",
#         "negative": "We oppose banning single-use plastics because it burdens low-income households."
#     }
    
#     for speech in generate_before_context(student_stance="negative", student_role=2, team_lines=team_lines):
#         print(f"{speech['stance']} {speech['speaker_role']}: {speech['text'][:100]}...")

if __name__ == "__main__":
    team_lines = {
        "affirmative": "We support banning single-use plastics because they cause irreversible environmental harm.",
        "negative": "We oppose banning single-use plastics because it burdens low-income households."
    }
    
    before_speeches = list(generate_before_context(student_stance="negative", student_role=2, team_lines=team_lines))
    
    student_speech = "We believe the ban is necessary because plastic pollution is an urgent environmental crisis."
    
    for speech in generate_after_context(
        student_stance="negative",
        student_role=2,
        student_speech=student_speech,
        team_lines=team_lines,
        previous_speeches=before_speeches
    ):
        print(f"{speech['stance']} {speech['speaker_role']}: {speech['text'][:100]}...")