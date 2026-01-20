"""PDF Highlighting Module

Provides functions to search and highlight names in PDF schedules.
Uses PyMuPDF (fitz) for permanent highlighting with case-sensitive exact text matching.
"""

import fitz  # PyMuPDF
import json
import os
from typing import List, Dict, Tuple


SETTINGS_FILE = "highlight_settings.json"


def load_highlight_settings() -> Dict:
    """Load highlighting configuration from JSON file.
    
    Returns default settings if file doesn't exist.
    """
    default_settings = {
        "names": [
            {"name": "Pr. E. Grau", "color": "#FFFF00", "enabled": True},
            {"name": "Dc. Marcus Grau", "color": "#00FF00", "enabled": True}
        ],
        "settings": {
            "auto_highlight_on_download": True,
            "create_copy": False,
            "highlight_opacity": 0.5
        }
    }
    
    if not os.path.exists(SETTINGS_FILE):
        save_highlight_settings(default_settings)
        return default_settings
    
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading highlight settings: {e}")
        return default_settings


def save_highlight_settings(settings: Dict) -> bool:
    """Save highlighting configuration to JSON file.
    
    Args:
        settings: Dictionary containing names and settings
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving highlight settings: {e}")
        return False


def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """Convert hex color to RGB tuple (0-1 range for PyMuPDF).
    
    Args:
        hex_color: Hex color string like "#FFFF00"
        
    Returns:
        Tuple of (r, g, b) values in 0-1 range
    """
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b)


def clear_highlights_from_pdf(pdf_path: str, remove_yellow_backgrounds: bool = True) -> int:
    """Remove all highlight colors (custom highlights + yellow backgrounds) from a PDF.
    
    This removes:
    - Highlight annotations (legacy)
    - Yellow backgrounds (1 1 0 in content stream)  
    - Custom highlight colors from cell backgrounds
    
    Args:
        pdf_path: Path to the PDF file
        remove_yellow_backgrounds: If True, also remove colored backgrounds from content
        
    Returns:
        Number of items removed
    """
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        return 0
    
    try:
        # First pass: Remove annotation highlights using PyMuPDF (legacy support)
        doc = fitz.open(pdf_path)
        removed_count = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Remove annotation-based highlights
            annots = page.annots()
            if annots:
                for annot in annots:
                    # Check if it's a highlight annotation
                    # Type 4 = Square (our rect annotations)
                    # Type 8 = Highlight, 9 = Underline, 10 = Squiggly, 11 = StrikeOut
                    if annot.type[0] in (4, 8, 9, 10, 11):
                        page.delete_annot(annot)
                        removed_count += 1
        
        # Save temporary file
        temp_path = pdf_path + ".temp"
        doc.save(temp_path)
        doc.close()
        
        # Second pass: Remove all highlight colors using PyPDF content stream editing
        if remove_yellow_backgrounds:
            from pypdf import PdfReader, PdfWriter
            from pypdf.generic import DecodedStreamObject
            
            # Load highlight settings to get all configured colors
            settings = load_highlight_settings()
            highlight_colors = set()
            
            # Add yellow (original background color to remove)
            highlight_colors.add((1.0, 1.0, 0.0))
            
            # Add all configured highlight colors
            for name_entry in settings.get('names', []):
                color_hex = name_entry.get('color', '')
                if color_hex:
                    rgb = hex_to_rgb(color_hex)
                    highlight_colors.add(rgb)
            
            reader = PdfReader(temp_path)
            writer = PdfWriter()
            
            for page in reader.pages:
                # Get the raw content bytes
                content = page.get_contents()
                if content is not None:
                    content_bytes = content.get_data()
                    original_len = len(content_bytes)
                    
                    # Replace each highlight color with light grey (0.949)
                    # This matches the white/light grey row backgrounds
                    for r, g, b in highlight_colors:
                        # Format: "r g b rg" or "r g b RG"
                        old_fill = f"{r:.6g} {g:.6g} {b:.6g} rg".encode()
                        old_stroke = f"{r:.6g} {g:.6g} {b:.6g} RG".encode()
                        new_color = b"0.949 0.949 0.949"
                        
                        content_bytes = content_bytes.replace(old_fill, new_color + b" rg")
                        content_bytes = content_bytes.replace(old_stroke, new_color + b" RG")
                    
                    if len(content_bytes) != original_len:
                        # Create new content stream with modified colors
                        new_stream = DecodedStreamObject()
                        new_stream.set_data(content_bytes)
                        page.replace_contents(new_stream)
                        removed_count += 1
                
                writer.add_page(page)
            
            # Save final result
            with open(pdf_path, "wb") as f:
                writer.write(f)
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        else:
            # No yellow removal - just use the PyMuPDF result
            if os.path.exists(temp_path):
                os.replace(temp_path, pdf_path)
        
        return removed_count
        
    except Exception as e:
        print(f"Error clearing highlights from PDF {pdf_path}: {e}")
        import traceback
        traceback.print_exc()
        return 0


def clear_highlights_from_pdfs(pdf_paths: List[str]) -> Dict[str, int]:
    """Clear highlights from multiple PDFs.
    
    Args:
        pdf_paths: List of PDF file paths
        
    Returns:
        Dictionary mapping PDF path to number of highlights removed
    """
    results = {}
    
    for pdf_path in pdf_paths:
        if not pdf_path or not os.path.exists(pdf_path):
            continue
        
        count = clear_highlights_from_pdf(pdf_path)
        if count > 0:
            results[pdf_path] = count
            print(f"Cleared {count} highlight(s) from {os.path.basename(pdf_path)}")
    
    return results


def highlight_text_in_pdf(pdf_path: str, name: str, color: str, opacity: float = 0.35) -> int:
    """Search for exact text matches and add highlight annotations.
    
    Args:
        pdf_path: Path to the PDF file
        name: Exact text to search for (case-sensitive)
        color: Hex color string (e.g., "#FFFF00")
        opacity: Highlight opacity 0-1 (default 0.35 for good readability)
        
    Returns:
        Number of highlights added
    """
    if not os.path.exists(pdf_path):
        return 0
    
    try:
        doc = fitz.open(pdf_path)
        rgb_color = hex_to_rgb(color)
        highlight_count = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Search for exact text (case-sensitive)
            text_instances = page.search_for(name)
            
            for inst in text_instances:
                # Calculate dimensions of the original text box
                original_width = inst.x1 - inst.x0
                original_height = inst.y1 - inst.y0
                
                print(f"\n--- Found '{name}' on page {page_num + 1} ---")
                print(f"Original rect: x0={inst.x0:.2f}, y0={inst.y0:.2f}, x1={inst.x1:.2f}, y1={inst.y1:.2f}")
                print(f"Original WIDTH (x1-x0): {original_width:.2f}")
                print(f"Original HEIGHT (y1-y0): {original_height:.2f}")
                
                # For rotated text: visual width = y-direction, visual height = x-direction
                # Expand along the text length (y-direction) and shrink thickness (x-direction)
                expanded_rect = fitz.Rect(
                    inst.x0 + 0.5,    # Shrink thickness from left (visual top)
                    inst.y0 - 1,      # Expand length at start (visual left)
                    inst.x1 - 0.5,    # Shrink thickness from right (visual bottom)  
                    inst.y1 + 1       # Expand length at end (visual right)
                )
                
                # Calculate dimensions of the expanded box
                expanded_width = expanded_rect.x1 - expanded_rect.x0
                expanded_height = expanded_rect.y1 - expanded_rect.y0
                
                print(f"Expanded rect: x0={expanded_rect.x0:.2f}, y0={expanded_rect.y0:.2f}, x1={expanded_rect.x1:.2f}, y1={expanded_rect.y1:.2f}")
                print(f"Expanded WIDTH (x1-x0): {expanded_width:.2f}")
                print(f"Expanded HEIGHT (y1-y0): {expanded_height:.2f}")
                
                # Add rectangular annotation (not rounded like highlight)
                annot = page.add_rect_annot(expanded_rect)
                annot.set_colors(stroke=rgb_color, fill=rgb_color)
                annot.set_opacity(opacity)
                annot.set_border(width=0)  # No border
                annot.update()
                highlight_count += 1
        
        if highlight_count > 0:
            # Save to temp file first, then replace original
            temp_path = pdf_path + ".temp"
            doc.save(temp_path, deflate=True, garbage=4)
            doc.close()
            
            # Replace original with temp file
            import shutil
            shutil.move(temp_path, pdf_path)
        else:
            doc.close()
        
        return highlight_count
        
    except Exception as e:
        print(f"Error highlighting PDF {pdf_path}: {e}")
        return 0


def highlight_pdf_with_settings(pdf_path: str, settings: Dict = None) -> Dict[str, int]:
    """Apply all enabled highlights from settings to a PDF.
    
    Args:
        pdf_path: Path to the PDF file
        settings: Highlight settings dict (loads from file if None)
        
    Returns:
        Dictionary mapping name to highlight count
    """
    if settings is None:
        settings = load_highlight_settings()
    
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        return {}
    
    # Check if we should create a copy
    create_copy = settings.get('settings', {}).get('create_copy', False)
    target_path = pdf_path
    
    print(f"Create copy setting: {create_copy}")
    
    if create_copy:
        base, ext = os.path.splitext(pdf_path)
        target_path = f"{base} - Highlighted{ext}"
        print(f"Will create copy at: {target_path}")
        try:
            import shutil
            shutil.copy2(pdf_path, target_path)
            print(f"✓ Successfully created highlighted copy: {os.path.basename(target_path)}")
            
            # Clear yellow backgrounds FIRST before adding custom highlights
            print(f"Clearing yellow backgrounds from copy...")
            cleared = clear_highlights_from_pdf(target_path, remove_yellow_backgrounds=True)
            print(f"✓ Cleared {cleared} yellow background(s)")
            
        except Exception as e:
            print(f"✗ Error creating copy: {e}")
            target_path = pdf_path  # Fall back to original
    
    opacity = settings.get('settings', {}).get('highlight_opacity', 0.5)
    results = {}
    
    # Now add custom name highlights AFTER clearing yellow
    for name_entry in settings.get('names', []):
        if not name_entry.get('enabled', True):
            continue
        
        name = name_entry.get('name', '')
        color = name_entry.get('color', '#FFFF00')
        
        if name:
            count = highlight_text_in_pdf(target_path, name, color, opacity)
            results[name] = count
            if count > 0:
                print(f"Highlighted '{name}' {count} time(s) in {os.path.basename(target_path)}")
    
    return results


def process_schedule_pdfs(pdf_paths: List[str], settings: Dict = None) -> Dict[str, Dict[str, int]]:
    """Process multiple schedule PDFs with highlighting.
    
    Args:
        pdf_paths: List of PDF file paths
        settings: Highlight settings dict (loads from file if None)
        
    Returns:
        Dictionary mapping PDF path to highlight results
    """
    if settings is None:
        settings = load_highlight_settings()
    
    # Check if auto-highlight is enabled
    auto_highlight = settings.get('settings', {}).get('auto_highlight_on_download', True)
    if not auto_highlight:
        return {}
    
    all_results = {}
    
    for pdf_path in pdf_paths:
        if not pdf_path or not os.path.exists(pdf_path):
            continue
        
        # Only process schedule PDFs (not DSG documents)
        if 'schedule' in os.path.basename(pdf_path).lower():
            results = highlight_pdf_with_settings(pdf_path, settings)
            if results:
                all_results[pdf_path] = results
    
    return all_results
