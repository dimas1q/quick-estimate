SHELL := /bin/bash

.PHONY: up dev down down-dev restart restart-dev logs logs-dev ps ps-dev

DEFAULT_DEV_CONFIG_FILE := ./config/app.dev.toml
ifneq ("$(wildcard ./config/app.dev.local.toml)","")
DEFAULT_DEV_CONFIG_FILE := ./config/app.dev.local.toml
endif
DEV_CONFIG_FILE := $(if $(QE_DEV_CONFIG_FILE),$(QE_DEV_CONFIG_FILE),$(DEFAULT_DEV_CONFIG_FILE))
DEV_COMPOSE := QE_DEV_CONFIG_FILE="$(DEV_CONFIG_FILE)" docker compose -f docker-compose.dev.yml

up:
ifeq ($(filter dev,$(MAKECMDGOALS)),dev)
	$(DEV_COMPOSE) up --build
else
	docker compose up --build -d
endif

dev:
ifeq ($(filter up,$(MAKECMDGOALS)),up)
	@:
else
	$(DEV_COMPOSE) up --build
endif

down:
	docker compose down

down-dev:
	$(DEV_COMPOSE) down

restart:
	docker compose down && docker compose up --build -d

restart-dev:
	$(DEV_COMPOSE) down && $(DEV_COMPOSE) up --build

logs:
	docker compose logs -f --tail=200

logs-dev:
	$(DEV_COMPOSE) logs -f --tail=200

ps:
	docker compose ps

ps-dev:
	$(DEV_COMPOSE) ps
