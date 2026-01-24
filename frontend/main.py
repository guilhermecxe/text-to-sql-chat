from dotenv import load_dotenv
import streamlit as st
import logging
import os

from views.sidebar_view import show_sidebar

load_dotenv()

# Controle de logs
MODE = os.getenv("MODE")
logging.basicConfig(
    level=(logging.DEBUG if MODE == "dev" else logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.getLogger("watchdog").setLevel(logging.WARNING)


# Controle de páginas
pages = [
    st.Page(page="views/chat_view.py", title="Conversational Agent")
]

# Sidebar
show_sidebar()

pg = st.navigation(pages)
pg.run()