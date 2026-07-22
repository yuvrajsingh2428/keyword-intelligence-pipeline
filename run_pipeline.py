#!/usr/bin/env python3
"""Entry point for running the Keyword Intelligence Pipeline from the command line."""

import sys
from pathlib import Path

# Add the project root to the path so modules can be resolved
root = Path(__file__).parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from keyword_intelligence.interfaces.cli_runner import CliRunner

if __name__ == "__main__":
    runner = CliRunner()
    runner.execute(sys.argv[1:])
