.PHONY: help install test lint format run docker-build docker-run deploy clean

help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linters"
	@echo "  make format      - Format code"
	@echo "  make run         - Run API locally"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run  - Run Docker container"
	@echo "  make deploy      - Deploy to GCP (requires env vars)"
	@echo "  make clean       - Clean cache files"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

lint:
	flake8 app/ tests/ --max-line-length=100 --extend-ignore=E203,W503
	black --check app/ tests/
	isort --check-only app/ tests/

format:
	black app/ tests/
	isort app/ tests/

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

docker-build:
	docker build -t clinical-bert-api .

docker-run:
	docker run -p 8000:8000 clinical-bert-api

deploy:
	@if [ -z "$$GCP_PROJECT_ID" ]; then \
		echo "Error: GCP_PROJECT_ID not set"; \
		exit 1; \
	fi
	./deploy.sh

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -exec rm -r {} +
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info

