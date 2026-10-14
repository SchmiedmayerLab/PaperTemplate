# SPDX-FileCopyrightText: 2026 Schmiedmayer Lab and the project authors (see CONTRIBUTORS.md)
#
# SPDX-License-Identifier: MIT

PYTHON := PYTHONDONTWRITEBYTECODE=1 python3
SUBFILE ?= paper/sections/10_introduction.tex
PREVIEW := paper/preprint-preview.tex
ARXIV_DATE ?=

.PHONY: all ci doctor submodules submodule-check pdf preview-pdf subfile subfile-clean check tex-check reproducibility-check reproduce submission-check arxiv arxiv-check references word-count license-check links compliance clean distclean

all: check reproduce pdf

ci: check reproduce pdf preview-pdf

doctor:
	$(PYTHON) tools/scripts/check_tools.py

submodules:
	git submodule update --init --recursive

submodule-check:
	$(PYTHON) tools/scripts/check_submodules.py

pdf:
	latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex

preview-pdf:
	latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error $(PREVIEW)

subfile:
	latexmk -cd -pdf -interaction=nonstopmode -halt-on-error -file-line-error -auxdir=../../build -outdir=../../build $(SUBFILE)

subfile-clean:
	latexmk -cd -C -auxdir=../../build -outdir=../../build $(SUBFILE)

check:
	$(PYTHON) -m unittest discover -s tools/tests
	$(PYTHON) tools/scripts/check_project.py
	$(PYTHON) tools/scripts/check_submodules.py
	$(PYTHON) tools/scripts/check_reproducibility.py
	$(PYTHON) tools/scripts/regenerate_bib_from_references.py --check

reproducibility-check:
	$(PYTHON) tools/scripts/check_reproducibility.py

reproduce:
	$(PYTHON) tools/scripts/check_reproducibility.py --run

submission-check:
	$(PYTHON) tools/scripts/check_project.py --submission
	$(PYTHON) tools/scripts/regenerate_bib_from_references.py --check
	$(PYTHON) tools/scripts/check_reproducibility.py --submission --run
	$(PYTHON) tools/scripts/check_tex_references.py
	latexmk -C main.tex
	latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex

arxiv:
	$(PYTHON) tools/scripts/package_arxiv.py $(if $(ARXIV_DATE),--submission-date "$(ARXIV_DATE)")

tex-check:
	$(PYTHON) tools/scripts/check_tex_references.py

arxiv-check: tex-check
	$(PYTHON) tools/scripts/package_arxiv.py --smoke-test $(if $(ARXIV_DATE),--submission-date "$(ARXIV_DATE)")

references:
	$(PYTHON) tools/scripts/regenerate_bib_from_references.py --in-place
	$(PYTHON) tools/scripts/organize_references.py --report-only

word-count:
	texcount -inc -sum main.tex

license-check:
	reuse --no-multiprocessing lint

links:
	linkspector check

compliance: license-check links

clean:
	latexmk -c main.tex
	latexmk -c $(PREVIEW)

distclean:
	latexmk -C main.tex
	latexmk -C $(PREVIEW)
