## Execução

1. To start the API:
```shell
uvicorn api.src.main:app
```

2. To start the worker responsible for processing messages:
```shell
python -m api.src.worker
```

3. To start the frontend
```shell
streamlit run frontend/main.py
```

## TODOs:

[] Implement `api` and `frontend` as containers.