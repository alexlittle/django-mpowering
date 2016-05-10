.PHONY: deps python-deps test test-django lint database help

###################################
### Dependency building

deps: python-deps

python-deps:  ## Install all dependencies, for running app, dev, and testing
	pip install -r requirements/frozen.txt
	pip install -r requirements/test.txt

###################################
### Testing

test: test-django lint  ## Run Django tests and flake8

test-django:  ## Run Django tests
	./manage.py test orb

lint:  ## Run flake8 over app
	flake8 orb

###################################
### Language
makemessages:  ## Make PO messages files
	./manage.py makemessages -l es -l pt_BR

###################################
### Building project components

build: python-deps node-deps database templates docs  ## Run all build commands, including dependencies, database, assets, and docs

docs:  ## Rebuild the documentation and open in default browser
	cd docs && make html
	@echo "\033[95m\n\nBuild successful! View the docs homepage at docs/_build/html/index.html.\n\033[0m"
	open docs/_build/html/index.html

database:  ## Migrate the database
	@echo "Setting up and updating the database..."
	./manage.py migrate --noinput

help:
	@perl -nle'print $& if m{^[a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
