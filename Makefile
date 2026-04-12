PYTHON ?= .venv/bin/python
PIPX ?= pipx
PROMPT ?= quanto é 1+1 responda somente o valor
MODEL ?= gpt
LOG ?=
REMOTE_REPO ?=
REMOTE_REF ?=

.PHONY: test prompt chat install install-local install-remote

test:
	$(PYTHON) -m pytest tests/unit

prompt:
	$(PYTHON) -m adapta.cli $(if $(LOG),--log $(LOG),) prompt --model $(MODEL) --prompt "$(PROMPT)"

chat:
	$(PYTHON) -m adapta.cli $(if $(LOG),--log $(LOG),) chat --model $(MODEL)

install:
	sh scripts/install-local.sh

install-local:
	PYTHON=$(PYTHON) sh scripts/install-local.sh

install-remote:
	sh scripts/install-remote.sh $(REMOTE_REPO) $(REMOTE_REF)
