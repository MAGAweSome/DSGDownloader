import subprocess
import sys
import os

# Optional: If you want to make sure you are in the right starting folder
# os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("\n--- Highlighting Names in PDFs ---")

# This command tells your computer: 
# "Use the current Python version to run the script found in tools/auto_highlight.py"
subprocess.run([sys.executable, "tools/auto_highlight.py"])