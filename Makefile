.PHONY: test audit regression paper paper-clean paper-flatten

PYTHON := python

install:
	$(PYTHON) -m pip install -e .

test:
	PYTHONPATH=$(CURDIR)/src $(PYTHON) -m pytest -q

audit:
	PYTHONPATH=$(CURDIR)/src $(PYTHON) -m rewriteflat audit

regression:
	PYTHONPATH=$(CURDIR)/src $(PYTHON) scripts/run_regression_harness.py

paper:
	mkdir -p paper/build
	if command -v latexmk >/dev/null 2>&1; then \
		cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build main.tex; \
	elif command -v pdflatex >/dev/null 2>&1; then \
		cd paper && pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build main.tex && pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build main.tex; \
	else \
		echo "missing TeX toolchain: need latexmk or pdflatex"; \
		exit 1; \
	fi
	$(MAKE) paper-flatten

paper-flatten:
	mkdir -p paper/build
	@flattener="$$(command -v latexpand || command -v texflatten || true)"; \
	if [ -z "$$flattener" ]; then \
		echo "missing LaTeX flattener: install latexpand or texflatten" >&2; \
		exit 1; \
	elif [ "$$(basename "$$flattener")" = "latexpand" ]; then \
		cd paper && "$$flattener" -o build/main_flat.tex main.tex; \
	else \
		cd paper && "$$flattener" main.tex > build/main_flat.tex; \
	fi

paper-clean:
	rm -rf paper/build
