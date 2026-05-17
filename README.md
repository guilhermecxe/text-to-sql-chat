# Conversational Agent with Database Access

A chat app where a conversational assistant answers questions and runs SQL queries against the **Chinook** music store database. The agent can also generate charts (bar, line, funnel) directly in the conversation.

Watch a demo:
<video src="media/demo.mp4" controls muted playsinline></video>


## Architecture

```
frontend (Streamlit)
    └── API Client → FastAPI (api/)
                        ├── POST /api/agents/ask-conversational-agent
                        ├── POST /api/agents/ask-sql-agent
                        └── GET  /api/agents/pull_answer

FastAPI
    ├── AgentDispatcherService  → Redis queue (enqueue jobs)
    └── AgentExecutorService    → Redis queue (dequeue + run agents)

Agents
    ├── ConversationalAgent     (LangGraph + checkpointing)
    │       ├── SQLAgent (subagent as tool)
    │       └── ChartToolkit (bar chart, line chart, funnel chart)
    └── SQLAgent                (LangChain SQLDatabaseToolkit → Chinook DB)

Adapters
    ├── RedisMessageBroker      (implements MessageBroker port)
    └── PlotlyChartDesigner     (implements ChartDesigner port)
```

The frontend supports **sync** and **async** modes. In async mode, requests are enqueued in Redis and polled via `pull_answer`.


## Environment setup

1. Create local `.env` files from the examples:
    ```shell
    cp api/.env.example api/.env
    cp frontend/.env.example frontend/.env
    ```
    Then edit both files and fill in the required keys and values.

2. Key variables in `api/.env`:

    | Variable | Description |
    |---|---|
    | `API_KEY` | Key required by the frontend to call the API (leave empty in dev) |
    | `MODE` | `dev` disables API key validation and enables debug logging |
    | `REDIS_HOST` / `REDIS_PORT` | Redis connection (use `redis` / `6379` inside Docker) |
    | `TASKS_QUEUE_NAME` | Redis list name for the job queue |
    | `OPENAI_API_KEY` | Required for the default `openai:gpt-4o-mini` model |
    | `GOOGLE_API_KEY` | Optional — for using Google models |
    | `LANGFUSE_*` | Optional — for observability traces |


## Quickstart

Build images and start the dev stack:
```shell
make build-dev
```


## Commands

| Command | Description |
|---|---|
| `make build-dev` | Build images and start the dev stack |
| `make up-dev` | Start the dev stack (no rebuild) |
| `make down-dev` | Stop the dev stack |
| `make reset-dev` | Stop the dev stack and remove volumes |
| `make logs-dev-api` | Follow API container logs |
| `make build-prod` | Build images and start the prod stack (includes Langfuse) |
| `make up-prod` | Start the prod stack (no rebuild) |
| `make down-prod` | Stop the prod stack |
| `make reset-prod` | Stop the prod stack and remove volumes |
| `make test` | Run the test suite via Docker |
| `make redis-cli-dev` | Open a Redis CLI session in the dev container |


## Charts

The conversational agent can generate charts inline. When a chart is produced, the agent references it in the message using the `[[chart=<id>]]` syntax. The frontend resolves these references to SVGs returned by the API alongside the answer.

Supported chart types: **bar**, **line**, **funnel**. Charts respect the active UI theme (`dark` / `light`).


## Observability

Langfuse traces are enabled when `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` are set in `api/.env`. In prod, start the Langfuse stack first with `make build-prod`.
