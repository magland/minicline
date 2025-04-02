# Deployment Instructions

This document outlines the steps to deploy minicline to PyPI.

## Prerequisites

- Python 3.8 or higher
- `build` and `twine` packages installed:
  ```bash
  python -m pip install --user build twine
  ```
- PyPI account with access rights to the minicline package

## Steps to Deploy

1. Update version in `pyproject.toml` and in __init__.py:
   ```toml
   [project]
   name = "minicline"
   version = "X.Y.Z"  # <-- Update this
   ```

   ```python
   __version__ = "X.Y.Z"  # <-- Update this
   ```
   Replace `X.Y.Z` with the new version number.

2. Build the distribution packages:
   ```bash
   python -m build
   ```
   This creates both wheel and source distribution in the `dist/` directory.

3. Verify the package files:
   ```bash
   python -m twine check dist/*
   ```
   Fix any warnings/errors before proceeding.

4. Upload to PyPI:
   ```bash
   python -m twine upload dist/*
   ```
   Enter your PyPI API token when prompted.

## Post-Deployment

1. Add and commit changes to the repository to __init__.py and pyproject.toml:
   ```bash
   git add minicline/__init__.py pyproject.toml
   git commit -m "Release vX.Y.Z"
   git push
   ```

2. Create and push a git tag for the release:
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

3. Clean up build artifacts:
   ```bash
   rm -rf build/ dist/ *.egg-info/
   ```
