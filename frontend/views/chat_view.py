from uuid import uuid4
import streamlit as st

from controllers.api_client import APIClient


if not st.session_state.get("api_client"):
    st.session_state["api_client"] = APIClient()

if not st.session_state.get("thread"):
    st.session_state.thread = []


# Adicionando a mensagem inicial da thread
with st.chat_message("ai"):
    st.markdown("""
**Olá!** Sou um assistente conversacional. Posso conversar como um chat moderno comum e 
também tenho acesso a um **SQL Agent** que interage com o banco de dados **Chinook** (uma base de loja de música).
Posso executar consultas SQL no Chinook e explicar os resultados em linguagem simples.

**Sugestões de perguntas:**
- "Quais são os 10 artistas com mais faixas?"
- "Quantas vendas tivemos por país?"
- "Quais são os gêneros mais populares?"
- "Mostre as faixas do álbum 'Let It Be' ou do artista 'The Beatles'."
- "Qual foi a receita por ano?"
                
:)
""")

# Mantendo as mensagens anteriores do chat
for message in st.session_state.thread:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Say something"):
    # Adicionando a mensagem do usuário à sessão
    message = {"role": "user", "content": prompt}
    st.session_state["thread"].append(message)

    if not st.session_state.get("thread_id"):
        st.session_state["thread_id"] = str(uuid4())

    with st.chat_message("user"):
        st.markdown(message["content"])

    # Processando a resposta
    api_client = st.session_state.get("api_client")
    with st.spinner("Thinking..."):
        answer = api_client.ask_conversational_agent(
            user_prompt=prompt,
            thread_id = st.session_state.get("thread_id")
        )

    with st.chat_message("ai"):
        st.write(answer)

    st.session_state["thread"].append({"role": "ai", "content": answer})