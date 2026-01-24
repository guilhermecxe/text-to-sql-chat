# Conversational Agent with Database Access

A lightweight chat app where a conversational assistant can answer questions and run SQL queries against the **Chinook** music store database.

The UI is a modern chat experience that shows real-time progress while the backend processes requests.

Watch a demo:
<video src="media/demo.mp4" controls muted playsinline></video>


## Environment setup

1. Create local `.env` files from the examples:
    ```shell
    cp api/.env.example api/.env
    cp frontend/.env.example frontend/.env
    ```
    - Then edit both files and fill in the required keys and connection values.

2. Clone the Langfuse repo:
    ```shell
    git clone https://github.com/langfuse/langfuse.git
    ```

## Quickstart

- Build the images and start the dev stack:
    ```shell
    make build-dev
    ```

### Other commands

- Starts the dev stack without rebuilding images:
    ```shell
    make up-dev
    ```

- Stops the dev stack containers:
    ```shell
    make down-dev
    ```

- Stops the dev stack and removes volumes:
    ```shell
    make reset-dev
    ```

- Builds images and starts the production stack (including Langfuse):
    ```shell
    make build-prod
    ```

- Starts the production stack without rebuilding images.
    ```shell
    make up-prod
    ```

- Stops the production stack containers:
    ```shell
    make down-prod
    ```

- Stops the production stack and removes volumes:
    ```shell
    make reset-prod
    ```

## Observability

For LLM interaction traces, register a project and generate keys in Langfuse.

Then add them to `api/.env` (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`). This enables viewing conversations and spans in the Langfuse dashboard.
