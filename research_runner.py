#!/usr/bin/env python3
"""Compatibility wrapper for the v0.1 research runner interface.

New integrations should use ``parallel-research fetch``.
"""

from parallel_research.cli import legacy_main

if __name__ == "__main__":
    legacy_main()
