.PHONY: install-mobile install-api mobile api api-test api-lint ml-test mobile-typecheck mobile-lint contracts structure

install-mobile:
	npm ci

install-api:
	python3 -m pip install -e "services/api[dev]"

mobile:
	npm run mobile:start

api:
	cd services/api && python3 -m uvicorn app.main:app --reload --host 0.0.0.0

api-test:
	cd services/api && python3 -m pytest

api-lint:
	python3 -m ruff check --config services/api/pyproject.toml services/api/app services/api/tests

ml-test:
	cd ml && python3 -m pytest

mobile-typecheck:
	npm run mobile:typecheck

mobile-lint:
	npm run mobile:lint

contracts:
	python3 scripts/export_openapi.py
	python3 scripts/generate_api_types.py

structure:
	python3 scripts/verify_structure.py
