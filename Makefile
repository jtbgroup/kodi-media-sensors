.PHONY: help config-check docker-up docker-down docker-restart docker-logs docker-shell tests lint clean

COMPOSE_FILE ?= .devcontainer/docker-compose.yml
PYTHON ?= python3

help:
	@echo "Kodi Media Sensors - Home Assistant Integration"
	@echo ""
	@echo "Available commands:"
	@echo "  make config-check    - Validate the Docker Compose configuration"
	@echo "  make docker-up       - Start Home Assistant"
	@echo "  make docker-down     - Stop Home Assistant"
	@echo "  make docker-restart  - Restart Home Assistant"
	@echo "  make docker-logs     - Follow Home Assistant logs"
	@echo "  make docker-shell    - Open a shell in the Home Assistant container"
	@echo "  make tests           - Run the test suite"
	@echo "  make lint            - Run Python lint checks"
	@echo "  make clean           - Stop containers and remove Python caches"
	@echo ""

config-check:
	docker compose -f $(COMPOSE_FILE) config

docker-up:
	docker compose -f $(COMPOSE_FILE) up -d
	@echo "Home Assistant is starting at http://localhost:8123"

docker-down:
	docker compose -f $(COMPOSE_FILE) down

docker-restart:
	docker compose -f $(COMPOSE_FILE) restart

docker-logs:
	docker compose -f $(COMPOSE_FILE) logs -f homeassistant

docker-shell:
	docker compose -f $(COMPOSE_FILE) exec homeassistant bash

tests:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m flake8 custom_components/kodi_media_sensors
	$(PYTHON) -m pylint custom_components/kodi_media_sensors

clean:
	docker compose -f $(COMPOSE_FILE) down
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
