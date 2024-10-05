# Makefile for running mypy type checks, tests, flake8 checks, and ruff formatting

# Variables
PYTHON = python3
MYPY = mypy
MYPY_CONFIG = mypy.ini  
SOURCE_DIR = ./nikola  
TEST_DIR = ./tests  
TEST_RUNNER = pytest 
FLAKE8 = flake8 
RUFF = ruff  # Ruff linter/formatter

# Default target
.PHONY: all
all: check test lint format

# Check types with mypy
.PHONY: check
check:
	@echo "Running mypy type checks..."
	$(MYPY) --config-file $(MYPY_CONFIG) $(SOURCE_DIR)

# Run tests with pytest
.PHONY: test
test:
	@echo "Running tests..."
	$(TEST_RUNNER) $(TEST_DIR)

# Run flake8 checks
.PHONY: lint
lint:
	@echo "Running flake8 checks..."
	$(FLAKE8) $(SOURCE_DIR) $(TEST_DIR)

# Run ruff checks and formatting
.PHONY: format
format:
	@echo "Running Ruff for formatting and linting..."
	$(RUFF) check $(SOURCE_DIR) $(TEST_DIR)  # Change 'check' to 'fix' if you want to auto-fix issues

# Clean up (optional)
.PHONY: clean
clean:
	@echo "Cleaning up..."
	# You can add commands to remove unwanted files if needed

# Help
.PHONY: help
help:
	@echo "Makefile commands:"
	@echo "  check   - Run mypy type checks"
	@echo "  test    - Run tests using pytest"
	@echo "  lint    - Run flake8 checks on source and tests"
	@echo "  format   - Run Ruff for formatting and linting"
	@echo "  clean   - Clean up (optional)"
	@echo "  help    - Show this help message"
