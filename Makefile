.PHONY: generate validate bench analyze clean

# Rematerialize tasks/ grading/ reference/ from tasks.py
generate:
	python generate.py

# Suite self-check: buggy fails both tests, reference passes both
validate:
	python validate.py

# Run the full benchmark (override args: make bench ARGS="--tier 5")
bench:
	python run_bench.py $(ARGS)

# Open the results dashboard (needs: pip install -r requirements-analysis.txt)
analyze:
	jupyter lab analyze.ipynb

# Remove generated results (keeps the task tree)
clean:
	rm -rf results __pycache__
