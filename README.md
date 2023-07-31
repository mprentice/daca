# DACA(P): Design & Analysis of Computer Algorithms in Python

This project is a work-in-progress working through The Design and Analysis of
Computer Algorithms by Aho, Hopcroft, & Ullman.

I thought it would be interesting to implement the various machine abstractions
in Python, and play around a little in building a Pidgin Algol
interpreter/compiler and translators between the abstractions. The focus is on
implementing and playing around with the abstractions and algorithms.

## Development notes

### Makefile

A `Makefile` is provided. Show help and usage:

    make help

### Install tools (optional)

Install pinned versions of python and poetry with
[asdf](https://asdf-vm.com/):

    make asdf-install

This step is optional. Just ensure that you have python and poetry installed.

### Install dependencies

Install required dependencies with [poetry](https://python-poetry.org/):

    make poetry-install

### Run tests

Use [flake8](https://flake8.pycqa.org/en/latest/index.html) to perform code
linting, [mypy](https://mypy.readthedocs.io/en/stable/) to run type checks, and
[pytest](https://pytest.org) to run unit tests and generate a code coverage
report:

    make test

flake8 plugins `flake8-bugbear`, `flake8-black`, and `flake8-isort` provide
extra lint checks.
