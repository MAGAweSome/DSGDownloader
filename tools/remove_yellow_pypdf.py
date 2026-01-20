"""Test removing yellow using PyPDF2 content stream editing"""
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream
from pypdf.generic import NameObject
from io import BytesIO
import re

def remove_yellow_backgrounds(input_path, output_path):
    """Remove yellow backgrounds by editing PDF content stream"""
    reader = PdfReader(input_path)
    writer = PdfWriter()
    
    for page_num, page in enumerate(reader.pages):
        print(f"\nPage {page_num + 1}:")
        
        # Get the raw content bytes
        content = page.get_contents()
        if content is not None:
            content_bytes = content.get_data()
            
            # Replace yellow color commands with light grey (0.949)
            # Pattern: 1 1 0 rg (fill color)
            original_len = len(content_bytes)
            content_bytes = content_bytes.replace(b"1 1 0 rg", b"0.949 0.949 0.949 rg")
            content_bytes = content_bytes.replace(b"1 1 0 RG", b"0.949 0.949 0.949 RG")
            
            if len(content_bytes) != original_len:
                print(f"  Replaced yellow color commands")
                # Create new content stream
                from pypdf.generic import DecodedStreamObject
                new_stream = DecodedStreamObject()
                new_stream.set_data(content_bytes)
                page.replace_contents(new_stream)
            else:
                print(f"  No simple yellow commands found")
        
        writer.add_page(page)
    
    # Save
    with open(output_path, "wb") as f:
        writer.write(f)
    
    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    import os
    
    input_pdf = r"C:\Users\Eric\OneDrive\Documents\1. Church\DSG\2026\02 FEB\Schedules\February 2026 Kitchener Serving Schedule.pdf"
    output_pdf = r"C:\Users\Eric\OneDrive\Documents\1. Church\DSG\2026\02 FEB\Schedules\February 2026 Kitchener Serving Schedule_pypdf_test.pdf"
    
    if os.path.exists(input_pdf):
        remove_yellow_backgrounds(input_pdf, output_pdf)
        print("\nTest complete! Check the output file.")
    else:
        print(f"File not found: {input_pdf}")
