from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.tools import tool

from api.src.agents.prompts.sql_agent import system_prompt

def create_sql_agent(model: str, db_uri: str, debug: bool = False, as_tool=False):
	@tool
	def sql_agent(question: str):
		"""
        Query a read-only Chinook music database to answer questions about music data.
		Call this agent whenever you need to interact with the Chinook database.
		It is not allowed to perform actions that modify the database, just read queries.

        The database contains information about:
        - Artists,
        - Albums,
        - Tracks,
        - Genres,
        - Playlists
		- and others relates.

		Args:
            question: A natural language question about the music database.
			
		Rerturns:
            A concise, factual answer derived strictly from the database query results.
		"""
		interactions = agent.invoke({"messages": [{"role": "user", "content": question}]})
		return interactions["messages"][-1].content

	llm = init_chat_model(model)
	db = SQLDatabase.from_uri(db_uri)

	toolkit = SQLDatabaseToolkit(db=db, llm=llm)
	tools = toolkit.get_tools()
	# TODO: alter the run_query tool to avoid commands that
	# 		modify the database

	agent = create_agent(
		model=llm,
		tools=tools,
		system_prompt=system_prompt.format(
			dialect=db.dialect,
			top_k=5,
		),
		debug=debug
	)

	return sql_agent if as_tool else agent

