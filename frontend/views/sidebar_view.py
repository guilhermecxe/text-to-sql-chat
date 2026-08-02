import streamlit as st

def show_sidebar():
    with st.sidebar:
        st.toggle("Async Mode", key="async_mode")

        st.divider()
        body = (
            "This is an application developed by **Guilherme Alves**. "
            "You can reach me out at [Github](https://github.com/guilhermecxe) "
            "or [LinkedIn](https://www.linkedin.com/in/guilhermecxe).\n\n"
            "The code for this application is available [at this link](https://github.com/guilhermecxe/text-to-sql-chat)."
        )
        st.markdown(body)
        