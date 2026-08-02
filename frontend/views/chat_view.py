import streamlit as st
import logging
import time

from controllers.api_client import APIClient
from controllers.redis_client import RedisClient

PROGRESS_BAR_WIDTH = "stretch"

st.title("Conversational Agent")

if not st.session_state.get("api_client"):
    st.session_state["api_client"] = APIClient()
    st.session_state["redis_client"] = RedisClient()

if not st.session_state.get("thread"):
    st.session_state.thread = []

st.markdown(
    """
    <style>
    .stProgress {
        color: white;
        background-color: rgb(255, 75, 75);
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initial chat message
with st.chat_message("ai"):
    st.markdown("""
**Hi!** I am a conversational assistant. I can chat like a modern, standard chat interface and  
I also have access to a **SQL Agent** that interacts with the **Chinook** database (a music store database). 

Besides that, I can generate charts! So ask me anything about this database and I will answer in plain text
or with a chart, just say how you want it.

**Suggested questions:**
- "Who are the top 10 artists with the most tracks?"
- "Draw a chart of the sales per the top 10 countries"
- "What are the most popular genres?"
- "Show the tracks from the album 'Acústico MTV' from the band 'Os Paralamas do Sucesso'."
- "Draw a line chart with the revenue per year"
""")

# Keeping the previous chat messages at the chat display
for message in st.session_state.thread:
    with st.chat_message(message["role"]):
        if message["role"] == "ai":
            st.write(message["content"], unsafe_allow_html=True)
        else:
            st.markdown(message["content"])

if prompt := st.chat_input("Say something"):
    # Saving the user input
    message = {"role": "user", "content": prompt}
    st.session_state["thread"].append(message)

    # Displaying the user input at the chat
    with st.chat_message("user"):
        st.markdown(message["content"])

    # Helper instances
    api_client: APIClient = st.session_state.get("api_client")
    redis_client = st.session_state.get("redis_client")

    # Sending the user input to the backend
    async_mode = st.session_state.get("async_mode")
    with st.spinner("Processing your message...", width="stretch"):
        response = api_client.ask_conversational_agent(
            user_prompt=prompt,
            thread_id=st.session_state.get("thread_id"),
            async_mode=async_mode,
            theme=st.context.theme.get("type", "light"),
            # model=st.session_state.get("model"), # TODO: implement dynamic model
        )

        if async_mode:
            job_id = response["job_id"]
            result = {}
            while not result:
                time.sleep(5)
                result = api_client.pull_answer(job_id)

                if result and result.get("success"):
                    st.session_state["thread_id"] = result["thread_id"]
                    answer = result["answer"]
                    break
                elif result and not result.get("success"):
                    answer = result.get("error", "Sorry, we had a problem trying to communicate with the other side of the application :/")
                    break
        else:
            if not response.get("success"):
                answer = response.get("error", "Unknown error")
            else:
                st.session_state["thread_id"] = response["thread_id"]
                answer = response["answer"]
    
    # Displaying the AI answer
    with st.chat_message("ai"):
        st.write(answer, unsafe_allow_html=True)

    # Saving the AI answer
    st.session_state["thread"].append({"role": "ai", "content": answer})
