"""Test script for removing yellow backgrounds from PDFs"""
import fitz
import os

def remove_yellow_backgrounds(pdf_path):
    """Experimental function to remove yellow cell backgrounds"""
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        return
    
    # Create output path
    base, ext = os.path.splitext(pdf_path)
    output_path = f"{base}_no_yellow{ext}"
    
    doc = fitz.open(pdf_path)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        drawings = page.get_drawings()
        
        print(f"\nPage {page_num + 1}:")
        print(f"  Total drawings: {len(drawings)}")
        
        # Find yellow rectangles and grey backgrounds
        yellow_rects = []
        grey_colors = []
        
        for i, drawing in enumerate(drawings):
            fill = drawing.get('fill')
            rect = drawing.get('rect')
            if fill and rect:
                r, g, b = fill[0], fill[1], fill[2]
                
                # Is it yellow?
                if abs(r - 1.0) < 0.01 and abs(g - 1.0) < 0.01 and abs(b - 0.0) < 0.01:
                    yellow_rects.append((i, rect, drawing))
                    print(f"  Yellow #{i}: rect={rect}")
                # Is it grey (potential replacement)?
                elif 0.7 < r < 1.0 and abs(r - g) < 0.1 and abs(g - b) < 0.1:
                    grey_colors.append(fill)
        
        print(f"  Found {len(yellow_rects)} yellow rectangles")
        print(f"  Found {len(set(grey_colors))} unique grey colors: {set(grey_colors)}")
        
        if yellow_rects and grey_colors:
            # Use the darkest grey
            replacement_grey = min(set(grey_colors), key=lambda c: sum(c))
            print(f"  Using replacement color: {replacement_grey}")
            
            # Simpler approach: Just draw WHITE over yellow to hide it
            shape = page.new_shape()
            for idx, rect, drawing in yellow_rects:
                shape.draw_rect(rect)
                shape.finish(fill=(1, 1, 1))  # White to erase yellow
            shape.commit()
            
            # Then draw grey rectangles at same positions
            shape2 = page.new_shape()
            for idx, rect, drawing in yellow_rects:
                shape2.draw_rect(rect)
                shape2.finish(fill=replacement_grey)
            shape2.commit(overlay=False)  # Draw grey UNDER the white
            
            print(f"  Covered {len(yellow_rects)} yellow rectangles")
    
    # Save result
    doc.save(output_path)
    doc.close()
    print(f"\nSaved to: {output_path}")
    return output_path


if __name__ == "__main__":
    # Test on the Kitchener schedule
    pdf_path = r"C:\Users\Eric\OneDrive\Documents\1. Church\DSG\2026\02 FEB\Schedules\February 2026 Kitchener Serving Schedule.pdf"
    
    if os.path.exists(pdf_path):
        result = remove_yellow_backgrounds(pdf_path)
        print(f"\nTest complete! Check the output file to see if yellows are removed.")
    else:
        print(f"PDF not found: {pdf_path}")
        print("Please update the path in the script.")
