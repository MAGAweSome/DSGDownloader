import os
import json
import pathlib
import sys
from dotenv import load_dotenv

# Set up paths
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pdf_tools.highlighter import highlight_names_in_pdf

def main():
    load_dotenv()
    
    target_pdf = os.getenv("PDF_PATH", "").strip('"')
    opacity = float(os.getenv("HIGHLIGHT_OPACITY", 0.3))
    
    # Load the name/color mapping from .env
    color_config = os.getenv("MINISTER_COLORS", "{}")
    try:
        name_color_map = json.loads(color_config)
    except Exception as e:
        print(f"Error parsing MINISTER_COLORS: {e}")
        return

    if not target_pdf or not os.path.exists(target_pdf):
        print(f"Error: PDF not found at {target_pdf}")
        return

    print(f"Targeting: {os.path.basename(target_pdf)}")

    # Run the engine with the full map
    success = highlight_names_in_pdf(target_pdf, name_color_map, opacity)
    
    if success:
        print("--- All ministers highlighted in their respective colors! ---")
    else:
        print("--- Process finished, no names found. ---")

if __name__ == "__main__":
    main()