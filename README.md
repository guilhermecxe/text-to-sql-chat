# Conversational Agent with Database Access

A chat app where a conversational agent answers questions in plain language by running SQL queries against a database (**text-to-SQL**), and can **generate charts directly in the chat** to visualize the results.

Watch a demo:
<video src="https://github.com/guilhermecxe/text-to-sql-chat/raw/main/media/demo.mp4" controls muted playsinline></video>

## Main ideas

### For agents

- Isolate the SQL agent from the conversational agent (the SQL agent is a subagent/tool), so each agent can specialize in its own task and be powered by a cheaper model, since it won't carry multiple responsibilities.

### For charts

- Let the conversational agent generate charts inline and reference them freely in its answer — e.g. the agent can say `"Here's a chart of the top 5 artists: [[chart=123]]"`, and the frontend resolves `[[chart=123]]` to the SVG returned by the API alongside the answer.
- Let the agent reshow a previously generated chart, backed by a cache of every chart created during the conversation.
- Keep chart generation robust to the agent's output: the agent only supplies the data, all the rendering logic is already implemented and tested.
- Use a `ChartDesigner` port to decouple the agent from the charting library (Plotly, in this case). Charts can be generated without the agent knowing the underlying library, and the library can be swapped without touching agent code.
- Use a predefined color palette so agent-generated charts stay visually consistent with the UI theme (dark/light).
- Decouple the textual answer from the chart image in the API response, so the client can save and/or render the chart image however it sees fit.

## Tech stack

- **API**: FastAPI, LangChain / LangGraph, Redis (job queue)
- **Charts**: Plotly + Kaleido (SVG export)
- **Frontend**: Streamlit
- **Observability**: Langfuse
- **Infra**: Docker Compose

---

An example of answer given by the conversational agent:

```json
{
  "answer": "Here’s the chart for the top 10 countries by sales:\n\n[[chart=10]]\n And here's the chart for the top 5 artists by sales:\n\n[[chart=5]]",
  "charts": {
    "10": "<svg class=\"main-svg\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" width=\"900\" height=\"600\" style=\"\" viewBox=\"0 0 900 600\"><rect x=\"0\" y=\"0\" width=\"900\" ...",
    "11": "<svg class=\"main-svg\" xmlns=\"http://www.w3.org/2000/svg\" xmlns:xlink=\"http://www.w3.org/1999/xlink\" width=\"900\" height=\"600\" style=\"\" viewBox=\"0 0 900 600\"><rect x=\"0\" y=\"0\" width=\"900\" ..."
  }
}
```

## Architecture

```
frontend (Streamlit)
    └── APIClient → FastAPI (api/)
                        ├── POST /api/agents/ask-conversational-agent
                        ├── POST /api/agents/ask-sql-agent
                        └── GET  /api/agents/pull_answer

FastAPI
    ├── AgentDispatcherService  → Redis queue (enqueue jobs)
    └── AgentExecutorService    → Redis queue (dequeue + run agents)
                                → enforces a daily usage limit (data/usage.json)
                                   before invoking an agent

Agents
    ├── ConversationalAgent     (LangGraph + checkpointing)
    │       ├── SQLAgent (subagent as tool)
    │       └── ChartToolkit (bar chart, line chart, funnel chart)
    │              └── ChartService (caches generated charts by ID)
    └── SQLAgent                (LangChain SQLDatabaseToolkit → Chinook DB)

Ports & Adapters
    ├── MessageBroker port      → RedisMessageBroker adapter
    └── ChartDesigner port      → PlotlyChartDesigner adapter
```

The frontend supports **sync** and **async** modes. In async mode, requests are enqueued in Redis and polled via `pull_answer`.

Errors (e.g. the daily usage limit being reached, or an agent failure) are returned by `AgentExecutorService` as `{"error": ...}`, turned into HTTP 500 responses by the routes, and surfaced by `APIClient` as a friendly message in the chat.


## Environment setup

1. Create local `.env` files from the examples:
    ```shell
    cp api/.env.example api/.env
    cp frontend/.env.example frontend/.env
    ```

2. Then edit both files and fill in the required keys and values with the appropriate values indicated.

## Quickstart

Build the images and start the stack:
```shell
make build-up
```


## Commands

| Command | Description |
|---|---|
| `make build` | Build the images |
| `make up` | Start the stack (no rebuild) |
| `make build-up` | Build the images and start the stack |
| `make down` | Stop the stack |
| `make reset` | Stop the stack and remove volumes |
| `make logs-api` | Follow the API container logs |
| `make logs-frontend` | Follow the frontend container logs |
| `make test` | Run the test suite via Docker |
| `make redis-cli` | Open a Redis CLI session in the container |


## Observability

Langfuse traces are enabled when `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` are set in `api/.env`.
