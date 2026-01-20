import fitz

pdf_path = r"C:\Users\Eric\OneDrive\Documents\1. Church\DSG\2026\02 FEB\Schedules\February 2026 Kitchener Serving Schedule.pdf"
doc = fitz.open(pdf_path)
page = doc[0]
drawings = page.get_drawings()

yellows = []
backgrounds = []

for d in drawings:
    if d.get('fill') and d.get('rect'):
        fill = d['fill']
        if len(fill) >= 3:
            r, g, b = fill[0], fill[1], fill[2]
            y_pos = d['rect'].y0
            
            # Yellow?
            if abs(r - 1.0) < 0.01 and abs(g - 1.0) < 0.01 and abs(b - 0.0) < 0.01:
                yellows.append((y_pos, fill, d['rect']))
            # Grey/white background?
            elif 0.7 < r < 1.0 and abs(r - g) < 0.1 and abs(g - b) < 0.1:
                backgrounds.append((y_pos, fill))

print(f"Found {len(yellows)} yellows")
print(f"Found {len(backgrounds)} background rectangles\n")

# For each yellow, find closest background
for yy, yfill, yrect in yellows:
    closest = min(backgrounds, key=lambda x: abs(x[0] - yy))
    print(f"Yellow at Y={yy:.1f}, X={yrect.x0:.1f}-{yrect.x1:.1f}")
    print(f"  Closest BG at Y={closest[0]:.1f}, color=({closest[1][0]:.3f}, {closest[1][1]:.3f}, {closest[1][2]:.3f})")
    print()

doc.close()
