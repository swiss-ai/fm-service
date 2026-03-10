.PHONY: format check test dev

format:
	ruff check --fix backend/
	ruff format backend/

check:
	ruff check backend/
	ruff format --check backend/

test:
	pytest tests/ -v

dev:
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8080
