asdf: ## Install pinned versions of tool dependencies with asdf
	asdf install

clean: ## Remove compiled files
	find . -name '*.pyc' -delete

help: ## Show usage
	@echo "Usage: make <target>"
	@echo
	@echo "Targets:"
	@sed \
		-e '/^[a-zA-Z0-9_\-]*:.*##/!d' \
		-e 's/:.*##\s*/:/' \
		-e 's/^\(.\+\):\(.*\)/$(shell tput setaf 6)\1$(shell tput sgr0):\2/' \
		$(MAKEFILE_LIST) | column -c2 -t -s :

.PHONY: clean help
