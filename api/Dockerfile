# Versão base com Python 3.12 e UV pré-instalado
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Instalando dependências do Python
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache-dir --index-strategy unsafe-best-match -r requirements.txt

COPY . .

# Expõe a porta 8000 para a aplicação FastAPI
EXPOSE 8000

# Comando para iniciar a aplicação com reload habilitado
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]