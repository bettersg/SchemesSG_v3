import streamlit as st
from PIL import Image
import requests
from dotenv import load_dotenv
from chat import *
import pandas as pd
import os
from cleantext import clean_text
from bqlogic import save_query

# Set page tab display
st.set_page_config(
   page_title="Schemes V2",
   page_icon= '🔍',
   layout="wide",
   initial_sidebar_state="expanded",
)

# Example local Docker container URL
# url = 'http://api:8000'
# Example localhost development URL
# url = 'http://localhost:8000'
load_dotenv()
url = os.getenv('API_URL')

# Define a key for the text area widget
query_key = 'query_text'
data_key = 'data_table'
rel_score_key = "rel_score_key"

# Initialize the query text in session state if not already present
if query_key not in st.session_state and data_key not in st.session_state:
    st.switch_page("app.py")


# Put our project logo and search promptat the top of the side bar
with st.sidebar:
    # Create a two-column layout
    col1, col2 = st.columns([1, 3])

    with col1:
        # Display the image in the first column
        st.image("Logo.webp")  # Adjust width as needed

    with col2:
        # Display the description in the second column
        st.title('Check out the top 10 relevant schemes below!')

        if st.button('Start search over'):
            # Reset the text area by updating its value in session state
            # st.session_state[query_key] = "Hello world"
            st.session_state.clear()
            st.switch_page("app.py")

# Add some line breaks
st.sidebar.markdown(f"""

         ## Displaying search results for \"{st.session_state[query_key]}\" below:""")

# Instantiate an empty data frame to catch empty search results
data = pd.DataFrame()


st.session_state[query_key] = st.session_state[query_key]
st.session_state[rel_score_key] = st.session_state[rel_score_key]

rel_score = st.session_state[rel_score_key]
print(rel_score)
rel_score = int(0 if rel_score == 0 else rel_score/25)
print(rel_score)

if data_key not in st.session_state:
    # Get search results from API
    requer_url = url + clean_text(st.session_state[query_key])+"&similarity_threshold="+str(rel_score)
    print(requer_url)
    response = requests.get(requer_url)
    if response.status_code == 200:
        data = pd.DataFrame(response.json())
        query_id = save_query(st.session_state[query_key], response.json())
        st.session_state['query_id'] = query_id
        st.session_state[data_key] = data
    else:
        data = pd.DataFrame()
else:
    data = st.session_state[data_key]


if data.empty:
    st.sidebar.write("No information available")
else:
    for index, row in data.iterrows():
        description = row["Description"].strip().replace("\n", "")
        # image = Image.open(data["Image"])
        st.sidebar.write(f'### {row["Agency"]} - {row["Scheme"]} ([Link]({row["Link"]}))')
        with st.sidebar:
            # Create a two-column layout
            col1, col2 = st.columns([1, 3])
            with col1:
                # Display the image in the first column
                st.image(row['Image'])

            with col2:
                # Display the description in the second column
                st.markdown(description.replace("$", "\$"))

# Chatbot
chatbot(data)
