# lint

lint-black:
	poetry run black --check beancount_ing/ tests/

lint-flake8:
	poetry run flake8 beancount_ing/ tests/

lint: lint-black lint-flake8

fmt-black:
	poetry run black beancount_ing/ tests/

# tests

test-pytest:
	poetry run pytest tests/

test: test-pytest

.PHONY: fmt-black \
	lint lint-black lint-flake8 \
	test test-pytest
