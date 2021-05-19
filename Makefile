# lint

lint-black:
	poetry run black --check beancount_ing_diba/ tests/

lint-flake8:
	poetry run flake8 beancount_ing_diba/ tests/

lint: lint-black lint-flake8

fmt-black:
	poetry run black beancount_ing_diba/ tests/

# tests

test-pytest:
	poetry run py.test tests/

.PHONY: fmt-black lint lint-black lint-flake8 test-pytest
