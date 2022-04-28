#! /usr/bin/env python3

"""
The most advanced telegram games (gamee) hacker in github.

This module contains the main logic.
"""

import sys

if __name__ == "__main__":
    # Check if the user is using the correct version of Python
    python_version = sys.version.split()[0]

    if sys.version_info < (3, 4):
        print(
            "GameeHacker requires Python 3.4+\nYou are using Python %s, which is not supported by GameeHacker"
            % (python_version)
        )
        sys.exit(1)

    import gameeHacker

    gameeHacker.main()
