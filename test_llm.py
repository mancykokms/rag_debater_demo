import streamlit as st
from openai import OpenAI

st.title("OpenRouter Test")

client = OpenAI(
    base_url="https://token.sensenova.cn/v1",
    api_key=st.secrets["sensenova"]["api_key"],
)

if st.button("Ask a test question"):
    response = client.chat.completions.create(
        model="sensenova-6.7-flash-lite",
        messages=[
            {"role": "user", "content": "In one sentence, why is rebuttal important in debate?"}
        ],
    )
    st.write(response.choices[0].message.content)