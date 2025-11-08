#!/usr/bin/env python3
"""Main entry point for 3dsconv.

Supports both refactored and legacy implementations for validation.
Default: Refactored modular implementation
Legacy mode: --legacy flag uses original monolithic implementation
"""

import os
import sys


def main() -> None:
    """Main entry point with implementation selection.

    Usage:
        python -m dsconv input.cci              # Refactored (default)
        python -m dsconv --legacy input.cci     # Legacy/original
    """
    # Check for --legacy flag BEFORE full argument parsing
    # This allows legacy implementation to handle all args independently
    if "--legacy" in sys.argv or "--use-legacy" in sys.argv:
        # Remove the flag from argv
        sys.argv = [arg for arg in sys.argv if arg not in ("--legacy", "--use-legacy")]

        # Execute legacy.py file in a way that mimics being run as __main__
        # This preserves the module-level execution behavior of the original code
        legacy_path = os.path.join(os.path.dirname(__file__), "legacy.py")

        with open(legacy_path) as f:
            code = f.read()

        # Execute in a namespace that mimics being run as __main__
        namespace = {
            "__name__": "__main__",
            "__file__": legacy_path,
            "__package__": None,
        }

        exec(compile(code, legacy_path, "exec"), namespace)
        return

    # Otherwise, run refactored implementation
    from dsconv.cli.main import main as refactored_main

    return refactored_main()


if __name__ == "__main__":
    main()
