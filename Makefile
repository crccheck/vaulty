VERSION := $(shell cat VERSION)
ifeq ($(shell uname), Darwin)
	# Get this with: `brew install gnu-sed`
	SED = gsed
else
	SED = sed
endif

help: ## Shows this help
	@echo "$$(grep -h '#\{2\}' $(MAKEFILE_LIST) | sed 's/: #\{2\} /	/' | column -t -s '	')"


clean: ## Remove temporary files
	find . -name ".DS_Store" -delete
	rm -rf .cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf *.egg
	rm -rf *.egg-info
	rm -rf __pycache__
	rm -rf build
	rm -rf dist

test: ## Run test suite
	pytest --cov

tdd: ## Run the test suite with a watcher
	ptw -- -sxv

.PHONY: htmlcov
htmlcov:
	coverage html
	open htmlcov/index.html

.PHONY: version
version:
	@$(SED) -i -r /version/s/[0-9.]+/$(VERSION)/ setup.py
	@$(SED) -i -r /__version__/s/[0-9.]+/$(VERSION)/ vaulty.py

# Release instructions
# 1. bump VERSION file
# 2. run `make release`
# 3. `git push --tags origin master`
# 4. update release notes
release: clean version
	@-git commit -am "bump version to v$(VERSION)"
	@-git tag $(VERSION)
	@-pip install wheel > /dev/null
	python setup.py sdist bdist_wheel upload
