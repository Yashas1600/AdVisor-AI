.PHONY: test

test:
	PYTHONPATH=backend python3 -m pytest tests/ -v --tb=short
