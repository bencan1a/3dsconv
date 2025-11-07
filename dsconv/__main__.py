#!/usr/bin/env python3
"""
Entry point for running 3dsconv as a module: python -m 3dsconv
"""

import os


def main():
    """
    Main entry point for the 3dsconv command.

    This executes the 3dsconv.py script which contains all the conversion logic.
    We do this because the module name starts with a digit and can't be imported normally.
    """
    script_path = os.path.join(os.path.dirname(__file__), "3dsconv.py")

    # Read and execute the script
    with open(script_path) as f:
        code = f.read()

    # Execute in a namespace that mimics being run as __main__
    namespace = {
        "__name__": "__main__",
        "__file__": script_path,
        "__package__": None,
    }

    exec(compile(code, script_path, "exec"), namespace)


if __name__ == "__main__":
    main()
