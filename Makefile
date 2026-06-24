.PHONY: help docker-build docker-up docker-down docker-logs docker-shell tests lint clean

# Variables
COMPOSE_FILE ?= .devcontainer/docker-compose.yml
DOCKER_IMAGE ?= homeassistant/home-assistant:latest
CONTAINER_NAME ?= kodi-media-sensors-ha

help:
	@echo "Kodi Media Sensors - Home Assistant Integration"
	@echo "=============================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make docker-build    - Build the Docker image"
	@echo "  make docker-up       - Start Home Assistant container"
	@echo "  make docker-down     - Stop Home Assistant container"
	@echo "  make docker-restart     - Restart Home Assistant container"
	@echo "  make docker-logs     - Show container logs"
	@echo "  make docker-shell    - Open shell in running container"
	@echo "  make tests           - Run tests"
	@echo "  make lint            - Run code quality checks"
	@echo "  make clean           - Remove containers and volumes"
	@echo ""

# Docker targets
docker-build:
	docker compose -f $(COMPOSE_FILE) build

docker-up: docker-build
	docker compose -f $(COMPOSE_FILE) up -d
	@echo "Home Assistant is starting..."
	@echo "Access it at http://localhost:8123"

docker-down:
	docker compose -f $(COMPOSE_FILE) down

docker-restart:
	docker compose -f $(COMPOSE_FILE) restart

docker-restart2:
	# 1. Arrête le container
	docker compose -f $(COMPOSE_FILE) down

	# 2. Nettoie les caches Python
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

	# 3. (Optionnel) Supprime l'image Docker pour la reconstruire
	docker rmi kodi-media-sensors-ha_homeassistant 2>/dev/null || true

	# 4. Redémarre tout
	docker compose -f $(COMPOSE_FILE) up -d

	# 5. Attends 30 secondes pour que HA se recharge
	sleep 2

	# 6. Vérifie les logs
	docker compose -f $(COMPOSE_FILE) logs -f homeassistant

docker-logs:
	docker compose -f $(COMPOSE_FILE) logs -f

docker-shell:
	docker compose -f $(COMPOSE_FILE) exec homeassistant bash

# Development targets
tests:
	python -m pytest tests/ -v

lint:
	@echo "Running code quality checks..."
	python -m pylint custom_components/kodi_media_sensors/ || true
	python -m flake8 custom_components/kodi_media_sensors/ || true

clean:
	docker compose -f $(COMPOSE_FILE) down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
