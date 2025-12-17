import streamlit as st
from dotenv import load_dotenv

load_dotenv()

pages = [
    st.Page(page="views/chat_view.py", title="Chat")
]

pg = st.navigation(pages)
pg.run()