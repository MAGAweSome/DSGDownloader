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
    """Remove all highlight annotations and optionally yellow backgrounds from a PDF.
    
    Args:
        pdf_path: Path to the PDF file
        remove_yellow_backgrounds: If True, also remove yellow filled rectangles from content
        
    Returns:
        Number of items removed (annotations + backgrounds)
    """
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
        return 0
    
    try:
        doc = fitz.open(pdf_path)
        removed_count = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Remove annotation-based highlights
            annots = page.annots()
            if annots:
                for annot in annots:
                    # Check if it's a highlight annotation
                    # Type 8 = Highlight, 9 = Underline, 10 = Squiggly, 11 = StrikeOut
                    if annot.type[0] in (8, 9, 10, 11):
                        page.delete_annot(annot)
                        removed_count += 1
            
            # Remove yellow background rectangles from content stream
            if remove_yellow_backgrounds:
                # First, analyze all background rectangles to find the alternating pattern
                drawings = page.get_drawings()
                
                # Collect all background colors with their Y positions
                bg_colors_by_y = {}
                yellow_positions = []
                
                for drawing in drawings:
                    if drawing.get('fill'):
                        fill = drawing['fill']
                        if len(fill) >= 3:
                            r, g, b = fill[0], fill[1], fill[2]
                            rect = drawing.get('rect')
                            
                            # Check if it's a highlight color (yellow, etc.)
                            is_highlight = (
                                (r > 0.7 and g > 0.7 and b < 0.4) or  # Yellow
                                (r > 0.8 and g > 0.5 and b < 0.4) or  # Orange  
                                (r < 0.4 and g > 0.7 and b < 0.4) or  # Green
                                (r > 0.8 and g < 0.4 and b > 0.7) or  # Pink
                                (r < 0.4 and g > 0.5 and b > 0.8)     # Cyan
                            )
                            
                            # Don't use black/very dark colors as replacement backgrounds
                            is_black = (r < 0.1 and g < 0.1 and b < 0.1)
                            
                            if rect:
                                y_pos = rect.y0
                                if is_highlight:
                                    yellow_positions.append((y_pos, fill))
                                elif not is_black:
                                    # Store non-highlight, non-black colors to learn the pattern
                                    bg_colors_by_y[y_pos] = fill
                
                if yellow_positions:
                    # Clean the page content
                    page.clean_contents()
                    
                    # Get the raw content stream
                    xref = page.get_contents()[0]
                    cont = doc.xref_stream(xref).decode()
                    
                    # Parse and replace yellow fills
                    lines = cont.split('\n')
                    new_lines = []
                    current_rect_y = None
                    i = 0
                    
                    while i < len(lines):
                        line = lines[i].strip()
                        
                        # Track rectangle definitions to get Y position
                        if 're' in line:
                            parts = line.split()
                            if len(parts) >= 5:
                                try:
                                    y_pos = float(parts[1])
                                    current_rect_y = y_pos
                                except:
                                    pass
                        
                        # Look for yellow color setting
                        if 'rg' in line:
                            parts = line.split()
                            if len(parts) >= 4 and parts[-1] == 'rg':
                                try:
                                    r, g, b = float(parts[0]), float(parts[1]), float(parts[2])
                                    is_highlight = (
                                        (r > 0.7 and g > 0.7 and b < 0.4) or
                                        (r > 0.8 and g > 0.5 and b < 0.4) or
                                        (r < 0.4 and g > 0.7 and b < 0.4) or
                                        (r > 0.8 and g < 0.4 and b > 0.7) or
                                        (r < 0.4 and g > 0.5 and b > 0.8)
                                    )
                                    
                                    if is_highlight and current_rect_y is not None:
                                        # Find the closest non-highlight color at same Y position
                                        replacement_color = None
                                        min_diff = float('inf')
                                        
                                        for y, color in bg_colors_by_y.items():
                                            diff = abs(y - current_rect_y)
                                            if diff < min_diff and diff < 5:  # Within 5 units
                                                min_diff = diff
                                                replacement_color = color
                                        
                                        # Use the matching background color
                                        if replacement_color:
                                            new_lines.append(f"{replacement_color[0]} {replacement_color[1]} {replacement_color[2]} rg")
                                        else:
                                            # Fallback to white if no match found
                                            new_lines.append("1 1 1 rg")
                                        
                                        removed_count += 1
                                        i += 1
                                        continue
                                except:
                                    pass
                        
                        new_lines.append(lines[i])
                        i += 1
                    
                    # Update the page with filtered content
                    new_cont = '\n'.join(new_lines)
                    doc.update_stream(xref, new_cont.encode())
        
        if removed_count > 0:
            doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
        
        doc.close()
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


def highlight_text_in_pdf(pdf_path: str, name: str, color: str, opacity: float = 0.5) -> int:
    """Search for exact text matches and add permanent highlights.
    
    Args:
        pdf_path: Path to the PDF file
        name: Exact text to search for (case-sensitive)
        color: Hex color string (e.g., "#FFFF00")
        opacity: Highlight opacity 0-1
        
    Returns:
        Number of highlights added
    """
    if not os.path.exists(pdf_path):
        print(f"PDF not found: {pdf_path}")
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
                # Add highlight annotation
                highlight = page.add_highlight_annot(inst)
                highlight.set_colors({"stroke": rgb_color, "fill": rgb_color})
                highlight.set_opacity(opacity)
                highlight.update()
                highlight_count += 1
        
        if highlight_count > 0:
            doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
        
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
    
    if create_copy:
        base, ext = os.path.splitext(pdf_path)
        target_path = f"{base} - Highlighted{ext}"
        try:
            import shutil
            shutil.copy2(pdf_path, target_path)
            print(f"Created highlighted copy: {target_path}")
        except Exception as e:
            print(f"Error creating copy: {e}")
            target_path = pdf_path  # Fall back to original
    
    opacity = settings.get('settings', {}).get('highlight_opacity', 0.5)
    results = {}
    
    # Process each enabled name
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
