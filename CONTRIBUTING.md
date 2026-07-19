# Contributing to Keyword Intelligence Pipeline

First off, thank you for considering contributing to the Keyword Intelligence Pipeline!

## Development Setup

1. Clone the repository
2. Set up a Python 3.11 virtual environment
3. Install dependencies: `pip install -e .[dev,test]`
4. Run tests: `pytest tests/`

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a build.
2. Update the README.md with details of changes to the interface, if applicable.
3. Increase the version numbers in any examples files and the README.md to the new version that this Pull Request would represent.
4. You may merge the Pull Request in once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the second reviewer to merge it for you.

## Code Style

- Use `ruff` for linting.
- Use `black` for formatting.
- Ensure strict typings with `mypy`.
