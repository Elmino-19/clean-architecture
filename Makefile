.DEFAULT_GOAL := help
COMPOSE := docker compose
DEPENDENCIES := database database-admin cache cache-admin

.PHONY: help
help:
	@grep -hE '^[a-zA-Z_-]+:' $(MAKEFILE_LIST) | cut -d: -f1 | sort -u

.PHONY: start
start:
	$(COMPOSE) up -d --build --remove-orphans
	$(COMPOSE) logs -f

.PHONY: start-silent
start-silent:
	$(COMPOSE) up -d --build --remove-orphans

.PHONY: stop
stop:
	$(COMPOSE) down --remove-orphans

.PHONY: delete
delete:
	$(COMPOSE) down -v --remove-orphans

.PHONY: dependencies-up
dependencies-up:
	$(COMPOSE) up -d --remove-orphans $(DEPENDENCIES)
	$(COMPOSE) logs -f $(DEPENDENCIES)

.PHONY: dependencies-up-silent
dependencies-up-silent:
	$(COMPOSE) up -d --remove-orphans $(DEPENDENCIES)

.PHONY: dependencies-down
dependencies-down:
	$(COMPOSE) down --remove-orphans

.PHONY: logs
logs:
	$(COMPOSE) logs -f

.PHONY: view-processes
view-processes:
	docker ps -a

.PHONY: dev
dev:
	uv run uvicorn app.app:app --reload

.PHONY: install
install:
	uv run python scripts/install.py

.PHONY: install-yes
install-yes:
	uv run python scripts/install.py --yes --project "$(p)"

.PHONY: opencode
opencode:
	uv run python scripts/opencode_setup.py --global

.PHONY: setup
setup:
	uv run python scripts/setup_env.py

.PHONY: setup-yes
setup-yes:
	uv run python scripts/setup_env.py --yes --project "$(p)"

.PHONY: env-check
env-check:
	uv run python scripts/setup_env.py --check

.PHONY: provision
provision:
	uv run python scripts/provision.py

.PHONY: provision-check
provision-check:
	uv run python scripts/provision.py --check

.PHONY: bootstrap
bootstrap: setup provision
	@echo ""
	@echo "Bootstrap complete. Start the stack with: make dependencies-up-silent && make dev"

.PHONY: doctor
doctor:
	uv run python scripts/doctor.py

.PHONY: test
test:
	uv run pytest

.PHONY: test-watch
test-watch:
	uv run pytest -f -q

.PHONY: rebrand
rebrand:
	uv run python scripts/rebrand.py "$(name)" --author "$(author)" --email "$(email)"

.PHONY: lint
lint:
	uv run ruff check .

.PHONY: format
format:
	uv run ruff format .

.PHONY: migrate
migrate:
	uv run alembic upgrade head

.PHONY: migration
migration:
	uv run alembic revision --autogenerate -m "$(m)"
