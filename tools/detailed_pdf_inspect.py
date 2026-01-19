"""Detailed PDF inspection to understand yellow backgrounds"""
import fitz
import sys

if len(sys.argv) < 2:
    print("Usage: python detailed_pdf_inspect.py <path_to_pdf>")
    sys.exit(1)

pdf_path = sys.argv[1]
doc = fitz.open(pdf_path)

print(f"Inspecting: {pdf_path}\n")

for page_num in range(min(1, len(doc))):  # Just first page
    page = doc[page_num]
    print(f"Page {page_num + 1}:")
    
    drawings = page.get_drawings()
    print(f"  Total drawings: {len(drawings)}\n")
    
    yellow_count = 0
    for i, drawing in enumerate(drawings):
        if drawing.get('fill'):
            fill = drawing['fill']
            if len(fill) >= 3:
                r, g, b = fill[0], fill[1], fill[2]
                # Check for yellowish
                if r > 0.7 and g > 0.7 and b < 0.4:
                    yellow_count += 1
                    print(f"  Drawing {i}:")
                    print(f"    Type: {drawing.get('type')}")
                    print(f"    Fill color (RGB): ({r:.2f}, {g:.2f}, {b:.2f})")
                    print(f"    Rect: {drawing.get('rect')}")
                    print(f"    Items: {drawing.get('items', [])[:3]}")  # First 3 items
                    print()
    
    print(f"  Yellow rectangles found: {yellow_count}\n")

doc.close()
