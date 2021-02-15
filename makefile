NAME = centralpy
SRC = ./${NAME}
PROMPT = ${NAME}


## List of makefile targets
## - help       : show this help documentation
.PHONY: help
help: makefile
	@sed -n 's/^.*##[ ]//p' $<

## - lint       : Run pylint on the source code
.PHONY: lint
lint: env
	. env/bin/activate && python3 -m pylint ${SRC}

## - black      : Run black on the source code
.PHONY: black
black: env
	. env/bin/activate && python3 -m black ${SRC}

## - env        : Set up the virtual environment
env: env/bin/activate

env/bin/activate: requirements.txt requirements-dev.txt
	test -d env || python3 -m venv --prompt ${PROMPT} env/
	. env/bin/activate && python3 -m pip install -r requirements.txt
	touch env/bin/activate

## - test       : Run unit tests
.PHONY: test
test:
	. env/bin/activate && python3 -m unittest discover -v

## - pypi       : Upload packages to PyPI
.PHONY: pypi
pypi: build
	. env/bin/activate && twine upload --repository-url https://upload.pypi.org/legacy/ dist/*;

## - pypi_test  : Upload packages to PyPI test
.PHONY: pypi_test
pypi_test: build
	. env/bin/activate && twine upload --repository-url https://test.pypi.org/legacy/ dist/*

## - build      : Build package artifacts
.PHONY: build
build: clean
	. env/bin/activate && python3 setup.py sdist bdist_wheel --universal

## - clean      : Remove artifacts from package building process
.PHONY: clean
clean:
	rm -rf ./dist;
	rm -rf ./build;
	rm -rf ./*.egg-info