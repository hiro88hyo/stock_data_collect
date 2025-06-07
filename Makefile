.PHONY: help install test lint format clean run docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  install       Install Python dependencies"
	@echo "  test          Run tests"
	@echo "  lint          Run linting checks"
	@echo "  format        Format code with black"
	@echo "  clean         Clean up generated files"
	@echo "  run           Run the application locally"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-run    Run Docker container"

install:
	uv add -r requirements.txt

test:
	PYTHONPATH=src pytest

lint:
	flake8 src/ --max-line-length=120 --exclude=__pycache__
	mypy src/ --ignore-missing-imports

format:
	black src/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	rm -rf htmlcov/
	rm -f .coverage

run:
	PYTHONPATH=src python src/main.py

docker-build:
	docker build -t stock-data-collector:latest .

docker-run:
	docker run -p 8080:8080 --env-file .env stock-data-collector:latest