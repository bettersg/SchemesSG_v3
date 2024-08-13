import streamlit as st
import random
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
import os
from dotenv import load_dotenv
from cleantext import clean_scraped_text
from bqlogic import save_chat_history

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def dataframe_to_text(df):
    # Example function to convert first 5 rows of a DataFrame into a text summary
    text_summary = ''
    for index, row in df.iterrows():
        cleanScrape = row['Scraped Text']
        sentence = clean_scraped_text(cleanScrape)

        text_summary += f"Scheme Name: {row['Scheme']}, Agency: {row['Agency']}, Description: {row['Description']}, Link: {row['Link']}, Scraped Text from website: {sentence}\n"
    return text_summary



# Streaming the responses
def response_generator(query, chat_history, topschemes):

    top_schemes_text = dataframe_to_text(topschemes)
    template = """
    As a virtual assistant, I'm dedicated to helping user navigate through the available schemes. User has done initial search based on their needs and system has provided top schemes relevant to the search. Now, my job is to advise on the follow up user queries based on the schemes data available by analyzing user query and extracting relevant answers from the top scheme data. Top Schemes Information includes scheme name, agency, Link to website, and may include text directly scraped from scheme website.

    In responding to user queries, I will adhere to the following principles:

    1. **Continuity in Conversation**: Each new question may build on the ongoing conversation. I'll consider the chat history to ensure a coherent and contextual dialogue.

    2. **Role Clarity**: My purpose is to guide user by leveraging the scheme information provided. My responses aim to advise based on this data, without undertaking any actions outside these confines.

    3. **Language Simplicity**: I commit to using simple, accessible English, ensuring my responses are understandable to all users, without losing the essence or accuracy of the scheme information.

    4. **Safety and Respect**: Maintaining a safe, respectful interaction is paramount. I will not entertain or generate harmful, disrespectful, or irrelevant content. Should any query diverge from the discussion on schemes, I will gently redirect the focus back to how I can assist with scheme-related inquiries.

    5. **Avoidance of Fabrication**: My responses will solely rely on the information from the scheme details provided, avoiding any speculative or unfounded content. I will not alter or presume any specifics not clearly indicated in the scheme descriptions.

    **User Query:**
    {user_question}

    **Chat History:**
    {chat_history}

    **Top Schemes Information:**
    """ + top_schemes_text

    # print(template)

    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", google_api_key=GOOGLE_API_KEY, temperature=0.3)

    chain = prompt | llm | StrOutputParser()

    return chain.stream({
        "chat_history": chat_history,
        "user_question": query
    })

def chatbot(topschemes):
    ai_intro = """
    🌟 Welcome to Scheme Support Chat! 🌟 Feel free to ask me questions like:
    - "Can you tell me more about Scheme X?"
    - "How can I apply for support from Scheme X?"

    To get started, just type your question below. I'm here to help explore schemes results 🚀
    """

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.chat_history = [AIMessage(ai_intro)]
        # with st.chat_message("AI"):
        #     st.markdown(AIMessage(ai_intro))

    for message in st.session_state.chat_history:
        if isinstance(message, HumanMessage):
            with st.chat_message("Human"):
                st.markdown(message.content)

        else:
            with st.chat_message("AI"):
                st.markdown(message.content)

    #Chat log
    prompt = st.chat_input("Ask any clarification questions for the search results...")

    if prompt is not None and prompt != "":
        # Append Human input
        st.session_state.chat_history.append(HumanMessage(prompt))

        # Display user message in chat message container
        with st.chat_message("Human"):
            st.markdown(prompt)

        # Display AI in chat message container
        with st.chat_message("AI"):
            ai_response = st.write_stream(response_generator(prompt, st.session_state.chat_history, topschemes))

        # Append AI response
        st.session_state.chat_history.append(AIMessage(ai_response))

        chat_exch = f"{HumanMessage(prompt).pretty_repr()} {AIMessage(ai_response).pretty_repr()}"
        print(f"======= Chat exchange ====== {chat_exch} =====")
        # Store the chat history in bigquery
        save_chat_history(st.session_state['query_id'], chat_exch)

    ### Create a native Streamlit reset button
    # st.markdown("### ")
