import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("Google Sheets Test")

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scopes
)
client = gspread.authorize(credentials)

if st.button("Write a test row"):
    sheet = client.open("debate-sparring-data").worksheet("results")
    sheet.append_row(["test_team", "test_motion", "affirmative", "test@student.com", "1", "{}", "[]", "False", "2026-07-20"])
    st.success("Row written! Check your Google Sheet.")

if st.button("Read all rows"):
    sheet = client.open("debate-sparring-data").worksheet("results")
    data = sheet.get_all_records()
    st.write(data)