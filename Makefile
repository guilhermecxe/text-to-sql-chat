PROJECT_NAME  = sql-agent-dev-app
LANGFUSE_NAME = sql-agent-prod-langfuse
DEV_NETWORK_NAME  = sql-agent-dev-network
PROD_NETWORK_NAME  = sql-agent-prod-network

.PHONY: help dev-network prod-network build-dev build-prod \
		up-dev up-prod down-dev down-prod reset-dev reset-prod

help:
	@echo "Targets disponíveis:"
	@echo "  make build-dev    - Build + up (dev)"
	@echo "  make build-prod   - Build + up (prod)"
	@echo "  make up-dev       - Sobe serviços (dev)"
	@echo "  make up-prod      - Sobe serviços (prod)"
	@echo "  make down-dev     - Derruba serviços (dev)"
	@echo "  make down-prod    - Derruba serviços (prod)"
	@echo "  make reset-dev    - Down + remove volumes (dev)"
	@echo "  make reset-prod   - Down + remove volumes (prod)"

dev-network:
	@docker network inspect $(DEV_NETWORK_NAME) >/dev/null 2>&1 || \
	docker network create $(DEV_NETWORK_NAME)

prod-network:
	@docker network inspect $(PROD_NETWORK_NAME) >/dev/null 2>&1 || \
	docker network create $(PROD_NETWORK_NAME)

build-dev: dev-network
	docker-compose -p $(PROJECT_NAME) -f docker-compose.yml up -d --build

build-prod: prod-network
	docker-compose -p $(LANGFUSE_NAME) -f langfuse/docker-compose.yml up -d --build
	docker-compose -p $(PROJECT_NAME) -f docker-compose-prod.yml up -d --build

up-dev:
	docker-compose -p $(PROJECT_NAME) -f docker-compose.yml up -d

up-prod:
	docker-compose -p $(LANGFUSE_NAME) -f langfuse/docker-compose.yml up -d
	docker-compose -p $(PROJECT_NAME) -f docker-compose-prod.yml up -d

down-dev:
	docker-compose -p $(PROJECT_NAME) -f docker-compose.yml down

down-prod:
	docker-compose -p $(LANGFUSE_NAME) -f langfuse/docker-compose.yml down
	docker-compose -p $(PROJECT_NAME) -f docker-compose-prod.yml down

reset-dev:
	docker-compose -p $(PROJECT_NAME) -f docker-compose.yml down -v

reset-prod:
	docker-compose -p $(LANGFUSE_NAME) -f langfuse/docker-compose.yml down -v
	docker-compose -p $(PROJECT_NAME) -f docker-compose-prod.yml down -v