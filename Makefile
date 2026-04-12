PYTHON ?= .venv/bin/python
PROMPT ?= quanto é 1+1 responda somente o valor
MODEL ?= gpt
LOG ?=

.PHONY: test prompt chat

test:
	$(PYTHON) -m pytest tests/unit

prompt:
	$(PYTHON) -m adapta.cli $(if $(LOG),--log $(LOG),) prompt --model $(MODEL) --prompt "$(PROMPT)"

chat:
	$(PYTHON) -m adapta.cli $(if $(LOG),--log $(LOG),) chat --model $(MODEL)
