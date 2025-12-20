import fitz  # PyMuPDF
import os

def highlight_names_in_pdf(pdf_path, name_color_map, opacity=0.5):
    if not os.path.exists(pdf_path):
        return False

    doc = fitz.open(pdf_path)
    found_any = False

    for page in doc:
        for name, color in name_color_map.items():
            clean_name = name.strip()
            if not clean_name: continue
                
            text_instances = page.search_for(clean_name)
            for inst in text_instances:
                found_any = True
                annot = page.add_rect_annot(inst)
                annot.set_colors(stroke=color, fill=color)
                annot.set_opacity(opacity)
                annot.set_border(width=0)
                annot.update()

    if found_any:
        temp_path = pdf_path + ".tmp"
        doc.save(temp_path)
        doc.close()
        os.remove(pdf_path)
        os.rename(temp_path, pdf_path)
        return True
    doc.close()
    return False