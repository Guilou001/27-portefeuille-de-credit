# Prérequis : uv (https://docs.astral.sh/uv/)
UV ?= uv

setup:
	$(UV) sync --locked --all-extras

test:             ## 20 tests fermés, sans réseau
	$(UV) run pytest

lint:
	$(UV) run ruff check .

all:              ## tout : vérification de l'annexe, coquilles, concentration, figures
	$(UV) run pcr tout
