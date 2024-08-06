import streamlit as st
from PIL import Image
import requests
from dotenv import load_dotenv
from chat import *
import pandas as pd
import os

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./schemesv2-frontend-write-bq-6f2c58dec79d.json"


# Set page tab display
st.set_page_config(
   page_title="Schemes V2",
   page_icon= '🔍',
   layout="centered",
#    layout="wide",
#    initial_sidebar_state="expanded",
)

# Title of the webpage
col1, col2 = st.columns([1, 3])
with col1:
    st.image("Logo.webp")
with col2:
    st.write("")
    st.title("Schemes V2",anchor=False)

st.markdown("""
        Hello! I'm your virtual assistant here to help you find schemes in Singapore for financial aid, healthcare, and more. I aim to provide relevant information and guide you to the best resources. As a volunteer-powered AI, I ensure safe and respectful advice based on the provided scheme data. Please verify the details with official sources for accuracy.
        """)
# Define a key for the text area widget
query_key = 'query_text'

# Initialize the query text in session state if not already present
if query_key not in st.session_state:
    st.session_state[query_key] = ""

# Display the text area with session state value
query = st.text_area(
        'Tell us the help you need. Don\'t give personal info.',
        value=st.session_state[query_key],
        key=query_key,
        placeholder='E.g. I am a dialysis patient in need of financial assistance and food support after being retrenched due to COVID 19'
    )

rel_score_key = "rel_score_key"
if rel_score_key not in st.session_state:
    st.session_state[rel_score_key] = 25

rel_score = st.slider('Show me schemes above relevance score of (0 - most lenient, 100 - most strict) :',
          0, 100,
          value=st.session_state[rel_score_key],
          step=25)
st.session_state[rel_score_key] = rel_score

if st.button(type="primary", label="🤖 Search & Chat", disabled=query==""):
    st.switch_page("pages/chat_page.py")
