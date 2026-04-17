"""Convenience runner for the DVRS engine test suite."""

from __future__ import annotations

import sys
import unittest


def main() -> int:
    try:
        import pytest
    except ImportError:
        pytest = None

    if pytest is not None:
        return int(pytest.main(["-p", "no:cacheprovider", "tests"]))

    suite = unittest.defaultTestLoader.discover("tests")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
