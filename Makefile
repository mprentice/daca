asdf: ## Install pinned versions of tool dependencies with asdf
	asdf install

clean: ## Remove compiled and build files
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -rf .mypy_cache

devinstall: ## Install dev & test dependencies
	poetry install

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
	poetry run mypy src

test: lint typecheck ## Run lint, typecheck, and unit tests

.PHONY: clean help lint typecheck test
