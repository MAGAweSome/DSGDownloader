"""Inspect PDF to see what types of highlighting/coloring exist"""
import fitz
import sys

if len(sys.argv) < 2:
    print("Usage: python inspect_pdf.py <path_to_pdf>")
    sys.exit(1)

pdf_path = sys.argv[1]
doc = fitz.open(pdf_path)

print(f"Inspecting: {pdf_path}\n")

for page_num in range(len(doc)):
    page = doc[page_num]
    print(f"Page {page_num + 1}:")
    
    # Check annotations
    annots = page.annots()
    if annots:
        print(f"  Annotations found: {len([a for a in annots])}")
        for annot in annots:
            print(f"    Type: {annot.type} - {annot.info.get('content', 'N/A')}")
    else:
        print("  No annotations found")
    
    # Check for colored rectangles/drawings in content stream
    drawings = page.get_drawings()
    if drawings:
        yellow_rects = []
        for drawing in drawings:
            # Check for filled rectangles with yellow-ish color
            if drawing.get('fill'):
                fill = drawing['fill']
                # Check if color is yellowish (high R and G, low B)
                if len(fill) >= 3 and fill[0] > 0.8 and fill[1] > 0.8 and fill[2] < 0.3:
                    yellow_rects.append(drawing)
        
        if yellow_rects:
            print(f"  Yellow filled rectangles in content: {len(yellow_rects)}")
    
    print()

doc.close()
