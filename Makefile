clean: ## Remove compiled and build files
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -f .coverage

install: ## Install dev & test dependencies
	poetry install --with=dev --with=test

help: ## Show usage
	@echo "Usage: make <target>"
	@echo
	@echo "Targets:"
	@sed \
		-e '/^[a-zA-Z0-9_\-]*:.*##/!d' \
		-e 's/:.*##\s*/:/' \
		-e 's/^\(.\+\):\(.*\)/$(shell tput setaf 6)\1$(shell tput sgr0):\2/' \
		$(MAKEFILE_LIST) | column -c2 -t -s : | sort

lint: ## Perform code linting
	poetry run flake8 src tests

typecheck: ## Perform static type analysis on src with mypy
	poetry run mypy -p daca

test: lint typecheck ## Run lint, typecheck, and unit tests
	poetry run pytest --cov=src tests

.PHONY: asdf-install clean help lint poetry-install test typecheck
