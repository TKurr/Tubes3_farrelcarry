# src/core/pattern_matching/__init__.py

# This file makes the 'pattern_matching' directory a Python package.
# It allows us to import its modules from other parts of the application.

# You can also use this file to conveniently expose a public API for the package.
from .pattern_matcher_factory import PatternMatcherFactory

__all__ = ["PatternMatcherFactory"]
