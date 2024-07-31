run:
	pixi run python -m pymenual

test:
	pixi run --environment test pytest -s

dev:
	pixi run python test.py
