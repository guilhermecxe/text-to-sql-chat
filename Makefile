PROJECT_NAME = sql-agent-dev-app
NETWORK_NAME = sql-agent-dev-network

.PHONY: help network build up build-up down reset logs-api logs-frontend test redis-cli

help:
	@echo "Targets disponíveis:"
	@echo "  make build         - Constrói as imagens"
	@echo "  make up            - Sobe os serviços"
	@echo "  make build-up      - Constrói e sobe os serviços"
	@echo "  make down          - Derruba os serviços"
	@echo "  make reset         - Down + remove os volumes"
	@echo "  make logs-api      - Exibe logs do serviço api"
	@echo "  make logs-frontend - Exibe logs do serviço frontend"
	@echo "  make test          - Executa a suite de testes (profile test)"
	@echo "  make redis-cli     - Abre um redis-cli no container"

network:
	@docker network inspect $(NETWORK_NAME) >/dev/null 2>&1 || \
	docker network create $(NETWORK_NAME)

build: network
	docker-compose -p $(PROJECT_NAME) -f docker-compose.yml build

up:
	docker-compose -p $(PROJECT_NAME) -f docker-compose.yml up -d

build-up: network
	docker-compose -p $(PROJECT_NAME) -f docker-compose.yml up -d --build

down:
	docker-compose -p $(PROJECT_NAME) -f docker-compose.yml down

reset:
	docker-compose -p $(PROJECT_NAME) -f docker-compose.yml down -v

logs-api:
	docker-compose -p $(PROJECT_NAME) -f docker-compose.yml logs -f api

logs-frontend:
	docker-compose -p $(PROJECT_NAME) -f docker-compose.yml logs -f frontend

test:
	docker-compose -p $(PROJECT_NAME) -f docker-compose.yml --profile test run --rm --build api-test

redis-cli:
	docker exec -it sql-agent-dev-redis redis-cli
