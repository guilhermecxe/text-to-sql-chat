## Execução

Para iniciar a API:
```shell
uvicorn api.src.main:app
```

Para iniciar o Worker responsável por processar as mensagens
```
python -m api.src.worker
```

Para iniciar o frontend:
```
streamlit run frontend/main.py
```