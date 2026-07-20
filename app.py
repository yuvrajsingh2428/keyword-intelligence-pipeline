import sys
from pathlib import Path

# Ensure the root directory is in the Python path
root = Path(__file__).parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

# Import and execute the main application UI
from keyword_intelligence.ui.app import main

if __name__ == "__main__":
    main()
