SHELL := /bin/bash

.PHONY: up dev down restart logs ps

up: dev

dev:
	docker compose up --build

down:
	docker compose down

restart:
	docker compose down && docker compose up --build

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps
