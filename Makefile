# lint

lint-black:
	poetry run black --check beancount_ing_diba/ tests/

lint-flake8:
	poetry run flake8 beancount_ing_diba/ tests/

lint: lint-black lint-flake8

# tests

test-pytest:
	poetry run py.test tests/

.PHONY: lint lint-black lint-flake8 test-pytest
