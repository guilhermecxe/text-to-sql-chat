from dotenv import load_dotenv
import streamlit as st
import logging
import os

load_dotenv()

# NOTE: Logs control
MODE = os.getenv("MODE")
logging.basicConfig(
    level=(logging.DEBUG if MODE == "dev" else logging.INFO),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.getLogger("watchdog").setLevel(logging.WARNING)


# NOTE: Pages control
pages = [
    st.Page(page="views/chat_view.py", title="Chat")
]

pg = st.navigation(pages)
pg.run()