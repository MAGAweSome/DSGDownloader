"""Test clearing highlights from a specific PDF"""
import sys
import os
sys.path.insert(0, r'C:\Users\Eric\OneDrive\Documents\Python Scripts\DSGDownloader')

from src.pdf_highlighter import clear_highlights_from_pdf

pdf_path = r"C:\Users\Eric\OneDrive\Documents\1. Church\DSG\2026\02 FEB\Schedules\February 2026 Kitchener Serving Schedule.pdf"

print(f"Testing clear on: {pdf_path}")
print(f"File exists: {os.path.exists(pdf_path)}")

count = clear_highlights_from_pdf(pdf_path)
print(f"\nCleared {count} items")
