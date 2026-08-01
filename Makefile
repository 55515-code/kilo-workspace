.PHONY: setup dev lint test clean

setup:
	bash scripts/setup.sh

dev:
	bash scripts/dev.sh

lint:
	bash scripts/lint.sh

test:
	bash scripts/test.sh

clean:
	rm -rf .venv node_modules dist build __pycache__
	find . -name "*.pyc" -delete

compose-up:
	docker compose up -d

compose-down:
	docker compose down

compose-with-db:
	docker compose --profile with-db up -d
