# Contributing to RMBench

Thank you for your interest in contributing to RMBench! This document provides guidelines for contributing to the project.

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow. Please be respectful and constructive in all interactions.

## How to Contribute

### Reporting Bugs

- Use the GitHub issue tracker
- Describe the bug in detail
- Include steps to reproduce
- Provide your environment details (OS, Python version, model used)

### Suggesting Enhancements

- Use the GitHub issue tracker
- Clearly describe the enhancement
- Explain why it would be useful
- Provide examples if possible

### Pull Requests

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Format code with black (`black .`)
7. Commit your changes (`git commit -am 'Add new feature'`)
8. Push to the branch (`git push origin feature/your-feature`)
9. Create a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/VenkataSudheer1863/RMBench.git
cd rmbench

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rmbench

# Run specific test file
pytest tests/test_attacks.py
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public functions/classes
- Keep functions focused and single-purpose
- Maximum line length: 100 characters

## Adding New Attacks

1. Create a new file in `rmbench/attacks/`
2. Inherit from `BaseAttack`
3. Implement required methods
4. Add tests in `tests/test_attacks.py`
5. Update documentation

## Adding New Defenses

1. Create a new file in `rmbench/defenses/`
2. Inherit from `BaseDefense`
3. Implement required methods
4. Add tests in `tests/test_defenses.py`
5. Update documentation

## Adding New Models

1. Add model integration in `rmbench/models/`
2. Register in `model_registry.py`
3. Test with benchmark suite
4. Document setup requirements

## Documentation

- Update relevant documentation in `docs/`
- Include docstrings with examples
- Update README.md if needed

## Research Ethics

This is a security research project. All contributions must:
- Be for defensive purposes only
- Not facilitate real-world attacks
- Follow responsible disclosure practices
- Include appropriate warnings and disclaimers

## Questions?

Open an issue or discussion on GitHub.

Thank you for contributing!
