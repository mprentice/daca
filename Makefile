clean: ## Remove compiled files
	find . -name '*.pyc' -delete

help: ## Show usage
	@echo "Usage: make <command>"
	@echo
	@echo "Commands:"
	@sed \
		-e '/^[a-zA-Z0-9_\-]*:.*##/!d' \
		-e 's/:.*##\s*/:/' \
		-e 's/^\(.\+\):\(.*\)/$(shell tput setaf 6)\1$(shell tput sgr0):\2/' \
		$(MAKEFILE_LIST) | column -c2 -t -s :

.PHONY: clean help
