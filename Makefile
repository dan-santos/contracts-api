SHELL := /bin/sh

.PHONY: up
up:
	docker compose up -d --wait --remove-orphans --build && docker compose logs -f app

.PHONY: down
down:
	docker compose down --remove-orphans

.PHONY: test
test:
	pytest
