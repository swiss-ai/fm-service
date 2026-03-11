.PHONY: install install-dev format check test dev

install:
	uv pip install -r backend/requirements.txt

install-dev:
	uv pip install -r backend/requirements-dev.txt

format:
	ruff check --fix backend/
	ruff format backend/

check:
	ruff check backend/
	ruff format --check backend/

test:
	pytest backend/tests/ -v

dev:
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8080
