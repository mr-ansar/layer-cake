# Makefile (layer-cake)
# - code test, code style, code coverage
# - package build, package push
# - doc build, doc spelling, doc push
# - show
# - help
# - presence of virtual env
# - required commands
# - library installed locally

LIBRARY_FOLDERS:=src/layer_cake
LIBRARY_FILES:=$(shell find $(LIBRARY_FOLDERS) -name "*.py" -print)

TEST_FOLDERS:=test
TEST_FILES:=$(shell find $(TEST_FOLDERS) -name "*.py" -print)

REPO:=`git config --get remote.origin.url`
BRANCH=`git branch --show-current`
COMMIT=`git rev-parse HEAD`
VERSION=`git tag | tail -1`

DOC_S3_BUCKET:=layer-cake-manual
DOC_VERSION:=$(VERSION)
DOC_LATEST=https://$(DOC_S3_BUCKET).s3.ap-southeast-2.amazonaws.com/$(DOC_VERSION)/index.html

# https://layer-cake.s3.ap-southeast-2.amazonaws.com/0.0.0/index.html

.PHONY: test package doc

# Code - unit tests, coding standard (incl docstrings) and
# test coverage.
REQUIRED_COMMAND+=pytest pycodestyle pydocstyle coverage

test: code_test code_coverage code_style

code_test:
	pytest test

code_coverage:
	coverage run -m pytest
	coverage json
	jq .totals.percent_covered_display coverage.json | sed 's/"//g' > coverage_percent
	PERCENT=`cat coverage_percent`; if test $$PERCENT -lt 75; then echo "amber"; elif test $$PERCENT -lt 85; then echo "brightgreen"; else echo "deepskyblue"; fi > coverage_colour
	coverage html

clean::
	rm -f .coverage coverage.json
	rm -rf htmlcov
	rm -f coverage_percent coverage_colour

code_style:
	pycodestyle src

clean::
	find src test -depth -type d -name "__pycache__" -exec rm -rf "{}" \;

# Packaging - build the package and push to a package
# repository. Automate the increment of a build
# number and injection of code tracking details
# into the package __init__.py file.
REQUIRED_COMMAND+=bump-version package-init rm find python
INIT_FILE:=src/layer_cake/__init__.py

package: package_build package_push

package_init:
	python3 template/cheetah-replace.py template/__init__.tmpl repo=$(REPO) branch=$(BRANCH) commit=$(COMMIT) version=$(VERSION) > $(INIT_FILE)

package_build: package_init code_coverage
	python3 template/cheetah-replace.py template/pyproject.tmpl documentation=$(DOC_LATEST) > pyproject.toml
	python3 template/cheetah-replace.py template/README.tmpl \
		coverage_percent=`cat coverage_percent` coverage_colour=`cat coverage_colour` \
		integration_status=passing integration_colour=cyan > README.md
	git tag | tail -1 > VERSION
	python3 template/version-after.py `cat VERSION`; echo
	rm -rf build dist
	find src -depth -type d -name "*.egg-info" -exec rm -rf "{}" \;
	python -m build
	#git commit -m "Auto-increment build number." --quiet VERSION $(INIT_FILE)

# pip install -i https://test.pypi.org/pypi/ --extra-index-url https://pypi.org/simple ansar-connect
package_push: find_shareable
	python -m twine upload --verbose --repository testpypi dist/*

# pip install ansar-connect
package_release: find_shareable
	python -m twine upload --verbose dist/*

clean::
	rm -rf build dist
	find src -depth -type d -name "*.egg-info" -exec rm -rf "{}" \;
	find . -depth -type d -name ".ansar-home" -exec rm -rf "{}" \;

# Documentation - construct materials for a static website,
# run quality checks and push to a public url.
REQUIRED_COMMAND+=sphinx-build aws

doc: package doc_examples doc_build doc_spelling doc_push

doc_examples:
	(cd doc/source; ./run-and-save)

doc_build:
	(cd doc; make html)

doc_spelling:
	(cd doc; sphinx-build -b spelling source build)

doc_push:
	aws s3 cp doc/build/html s3://$(DOC_S3_BUCKET)/$(DOC_VERSION) --recursive
	echo $(DOC_LATEST) > DOC_LATEST_LINK
	@echo go to $(DOC_LATEST)

clean::
	rm -rf doc/build

# Show - print current details about the files, commands, package
# and repo that might be useful. Includes a basic leading tag so
# you know where the output came from.
REQUIRED_COMMAND+=xdg-open

show: show_src show_test show_doc show_command show_version show_init show_repo

show_src:
	@for f in $(LIBRARY_FILES); do \
	echo "<S> $$f"; \
	done

show_test:
	@for f in $(TEST_FILES); do \
	echo "<T> $$f"; \
	done

show_coverage:
	@xdg-open file://$(PWD)/htmlcov/index.html

show_py:
	@find src test -name "*.py" -print | sed -e "s/^/<Y> /"

show_doc:
	@find doc -name "*.rst" -print | sed -e "s/^/<D> /"

show_command:
	@for c in $(REQUIRED_COMMAND); do \
	WHICH=`which $$c`; \
	echo "<C> $$c ($$WHICH)"; \
	done

show_version:
	@VERSIONED="python pip git"; \
	for c in $$VERSIONED; do \
	CV=`$$c --version`; \
	echo "<V> $$c ($$CV)"; \
	done

show_init:
	@cat $(INIT_FILE) | sed -e "s/^/<I> /"

show_repo:
	@git status --porcelain | sed -e "s/^ */<G> /"

# Scan the local repositories for shareable repos, i.e. folders
# that contain .git, PACKAGE and VERSION names. Output a table
# of likelies (shareable-repo.out) and print a warning about
# any nearlies.
SHAREABLE_REPO:=shareable-repo.out

find_shareable:
	@> $(SHAREABLE_REPO)
	@HERE=`pwd`; \
	SELF=`basename $$HERE`; \
	for GIT in ../*/.git; do \
		FOLDER=`dirname $$GIT`; \
		NAME=`basename $$FOLDER`; \
		if [ "$$NAME" != "$$SELF" ]; then \
			if [ -e "$$FOLDER/PACKAGE" -a -e "$$FOLDER/VERSION" ]; then \
				PACKAGE=`cat $$FOLDER/PACKAGE`; \
				VERSION=`tail -1 $$FOLDER/VERSION`; \
				echo "$$FOLDER:$$PACKAGE:$$VERSION" >> $(SHAREABLE_REPO); \
			else \
				echo "*** repo \"$$FOLDER\" has no PACKAGE or VERSION (ignored)"; \
			fi; \
		fi; \
	done

# Scan the likelies (generated above) for any dangling materials, i.e.
# every potentially contributing repo must be up-to-date with its
# remote before other operations can proceed, like packaging.
confirm_status:
	@HERE=`pwd`; \
	SELF=`basename $$HERE`; \
	while read FPV; do \
		FOLDER=`echo $$FPV | awk -F: '{print $$1}'`; \
		PACKAGE=`echo $$FPV | awk -F: '{print $$2}'`; \
		NAME=`basename $$FOLDER`; \
		STATUS=`cd $$FOLDER; git status --porcelain`; \
		if ! [ -z "$$STATUS" ]; then \
			echo "*** repo \"$$NAME\" (package \"$$PACKAGE\") not clean (cd, git commit, git push)"; \
		fi; \
	done < $(SHAREABLE_REPO); \
	STATUS=`git status --porcelain`; \
	if [ ! -z "$$STATUS" ]; then \
		echo "*** current repo \"$$SELF\" not clean (git commit, git push)"; \
		exit 1; \
	fi

# Compare the current installation of packages against the
# expected installation. Expected editables are defined by
# the contents of the REQUIRES file, expected installs by
# the contents of the REFERENCES file. Any mismatch and the
# operation fails with messages suggesting where the problem
# seems to be.
FROZEN_PACKAGE:=frozen-package.out		# Snapshot of currently installed packages.
EDITABLE_PACKAGE:=editable-repo.out		# The "-e" slice of above.
INSTALLED_PACKAGE:=installed-repo.out	# The "non -e" slice.
NOT_EDITABLE:=not-editable.flag			# Crude bool flags using files.
NOT_INSTALLED:=not-installed.flag
INSTALL_REQUIRES:=install-requires.out	# Each line describes a setup "install_requires" entry.

confirm_installs: find_shareable
	@rm -f $(NOT_EDITABLE) $(NOT_INSTALLED)
	@pip freeze > $(FROZEN_PACKAGE)
	@grep "^-e " $(FROZEN_PACKAGE) > $(EDITABLE_PACKAGE)
	@grep -v "^-e " $(FROZEN_PACKAGE) > $(INSTALLED_PACKAGE)
	@rm -f $(INSTALL_REQUIRES)
	@while read PKG; do \
		if ! grep ":$$PKG:" $(SHAREABLE_REPO) >> $(INSTALL_REQUIRES); then \
			echo "*** repo for required package $$PKG not detected (git clone, pip -e)"; \
			touch $(NOT_EDITABLE); \
		elif ! grep "=$$PKG$$" $(EDITABLE_PACKAGE) > /dev/null; then \
			echo "*** repo for required package \"$$PKG\" not installed for edit (pip -e)"; \
			touch $(NOT_EDITABLE); \
		fi; \
	done < REQUIRES
	@while read PKG; do \
		if ! grep "^$$PKG" $(INSTALLED_PACKAGE) > /dev/null; then \
			echo "*** referenced package \"$$PKG\" not installed (pip install)"; \
			touch $(NOT_INSTALLED); \
		fi \
	done < REFERENCES
	@if [ -e $(NOT_EDITABLE) ]; then \
		echo "*** resolve differences between cloned repos, editable packages and REQUIRES"; \
		echo "*** refer to the REQUIRES/$(EDITABLE_PACKAGE) (expected/detected) files"; \
	fi
	@if [ -e $(NOT_INSTALLED) ]; then \
		echo "*** resolve differences between virtual environment and REFEFENCES"; \
		echo "*** refer to the REFERENCES/$(INSTALLED_PACKAGE) (expected/detected) files"; \
	fi
	@if [ -e $(NOT_EDITABLE) -o -e $(NOT_INSTALLED) ]; then \
		rm -f $(NOT_EDITABLE) $(NOT_INSTALLED); \
		exit 1; \
	fi

# A sequence of pre-conditions before any of the rules and their
# recipes are actually performed. Tried coomand-line overrides
# but never worked convincingly. Intended for use around targets
# for installation of tools.

# Check to see if this make is running inside a virtual environment.
VIRTUAL_REQUIRED:=$(if $(VIRTUAL_ENV),,$(error "Virtual environment not detected"))

# Check to see if the library has been installed locally, i.e. for
# development.
# ANSAR_FROZEN:=$(shell pip freeze | grep "^-e.*ansar$$")
# ANSAR_INSTALLED:=$(if $(ANSAR_FROZEN),,$(error "Library not locally installed"))

# Check to see that all of the commands listed in REQUIRED_COMMAND are
# available to this make.
REQUIRED:=$(foreach exec,$(REQUIRED_COMMAND),\
        $(if $(shell which $(exec)),,$(error "No $(exec) in PATH")))
