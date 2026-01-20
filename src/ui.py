"""Simple UI helpers: terminal prompts plus optional Tkinter dialog.

Exports:
- `get_user_selection()` -> dict with keys used by main/actions modules.
"""

from typing import Set, Iterable, Dict, Any
import os
import json


def prompt_multichoice(prompt: str, choices: Iterable[str], defaults: Iterable[str] | None = None) -> Set[str]:
    print(prompt)
    choices = list(choices)
    for i, c in enumerate(choices, start=1):
        print(f"{i}) {c}")
    raw = input("Enter choices (comma-separated numbers or names) [Enter=defaults]: ").strip()
    if not raw:
        return set(defaults or [])
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    selected: Set[str] = set()
    for p in parts:
        if p.isdigit():
            idx = int(p) - 1
            if 0 <= idx < len(choices):
                selected.add(choices[idx])
            continue
        for c in choices:
            if p.lower() == c.lower():
                selected.add(c)
                break
    return selected


def prompt_languages(prompt: str, langs: Iterable[str], defaults: Iterable[str] | None = None) -> Set[str]:
    return prompt_multichoice(prompt, list(langs), defaults=defaults)


ENV_PATH = os.path.join(os.getcwd(), '.env')


def _load_json_env(key: str):
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_PATH)
    except Exception:
        pass
    v = os.environ.get(key)
    if not v:
        return None
    try:
        return json.loads(v)
    except Exception:
        return None


def _save_json_env(key: str, value: Any) -> None:
    try:
        from dotenv import set_key
        # convert nested sets to lists so JSON can serialize them
        def _to_jsonable(v):
            if isinstance(v, set):
                return list(v)
            if isinstance(v, dict):
                return {k: _to_jsonable(val) for k, val in v.items()}
            if isinstance(v, list):
                return [_to_jsonable(i) for i in v]
            return v

        serializable = _to_jsonable(value if value is not None else [])
        set_key(ENV_PATH, key, json.dumps(serializable))
    except Exception:
        # best-effort only
        pass


def get_user_selection() -> Dict[str, Any]:
    """Return a selection dict. Try Tkinter GUI (pre-filled from .env), else terminal.

    Returned dict keys:
    - selections: set[str]
    - bible_reading_langs: set[str]
    - full_dsg_langs: set[str]
    - se_dsg_langs: set[str]
    - foreword_langs: set[str]
    - bible_references_langs: set[str]
    - schedules_chosen: set[str]
    - schedules_sub: dict[str, set[str]]
    """
    # Default to all months if no preference saved
    all_months = ['January', 'February', 'March', 'April', 'May', 'June', 
                  'July', 'August', 'September', 'October', 'November', 'December']
    
    saved = {
        'selections': set(_load_json_env('DSG_UI_SELECTIONS') or []),
        'schedules_chosen': set(_load_json_env('DSG_UI_SCHEDULES_CHOSEN') or []),
        'schedules_sub': _load_json_env('DSG_UI_SCHEDULES_SUB') or {},
        'full_dsg_langs': set(_load_json_env('DSG_UI_FULL_DSG_LANGS') or []),
        'se_dsg_langs': set(_load_json_env('DSG_UI_SE_DSG_LANGS') or []),
        'bible_reading_langs': set(_load_json_env('DSG_UI_BIBLE_READING_LANGS') or []),
        'foreword_langs': set(_load_json_env('DSG_UI_FOREWORD_LANGS') or []),
        'bible_references_langs': set(_load_json_env('DSG_UI_BIBLE_REFERENCES_LANGS') or []),
        'auto_submit_enabled': _load_json_env('DSG_UI_AUTO_SUBMIT') if _load_json_env('DSG_UI_AUTO_SUBMIT') is not None else True,
        'selected_months': set(_load_json_env('DSG_UI_SELECTED_MONTHS') or all_months),
        'selected_years': set(_load_json_env('DSG_UI_SELECTED_YEARS') or [str(y) for y in range(2024, 2028)]),
    }

    # Try GUI
    try:
        import customtkinter as ctk
        from tkinter import colorchooser

        # Set appearance mode and theme
        ctk.set_appearance_mode("dark")  # Options: "dark", "light", "system"
        ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

        root = ctk.CTk()
        root.title('DSG Downloader - Configuration')
        root.geometry("900x700")
        
        # Track cancellation state
        cancelled = False
        result = None
        
        # Create tabview for tabs
        tabview = ctk.CTkTabview(root)
        tabview.pack(fill='both', expand=True, padx=10, pady=10)
        
        # ===== TAB 1: Download Options =====
        tabview.add("Download Options")
        tab_download = tabview.tab("Download Options")
        
        # Make tab scrollable
        scrollable_download = ctk.CTkScrollableFrame(tab_download)
        scrollable_download.pack(fill='both', expand=True, padx=5, pady=5)
        
        # ===== SECTION 1: Schedules =====
        schedule_frame = ctk.CTkFrame(scrollable_download)
        schedule_frame.pack(fill='x', padx=10, pady=(10, 5))
        
        ctk.CTkLabel(schedule_frame, text='📅 Schedules to Download', 
                    font=ctk.CTkFont(size=15, weight="bold")).pack(anchor='w', padx=15, pady=(15, 10))
        
        # Schedule groups with their sub-options in expandable sections
        schedule_options = ['District Serving Schedules', 'NACC Calendars', 'Youth Schedules', 'Seniors Schedules']
        sched_vars = {s: ctk.IntVar(value=1 if s in saved['schedules_chosen'] else 0) for s in schedule_options}
        
        # District Serving Schedules
        districts = ['British Columbia', 'Alberta', 'Saskatchewan', 'Manitoba', 'Northern Ontario', 'Kitchener', 'Hamilton', 'Toronto', 'Eastern Canada']
        district_vars = {d: ctk.IntVar(value=1 if d in (saved['schedules_sub'].get('District Serving Schedules') or []) else 0) for d in districts}
        
        district_frame = ctk.CTkFrame(schedule_frame)
        district_frame.pack(fill='x', padx=10, pady=5)
        ctk.CTkCheckBox(district_frame, text='District Serving Schedules', 
                       variable=sched_vars['District Serving Schedules'],
                       font=ctk.CTkFont(weight="bold")).pack(anchor='w', padx=10, pady=5)
        district_sub_frame = ctk.CTkFrame(district_frame, fg_color="transparent")
        district_sub_frame.pack(fill='x', padx=30, pady=(0, 5))
        for i, d in enumerate(districts):
            col = i % 3
            row = i // 3
            ctk.CTkCheckBox(district_sub_frame, text=d, variable=district_vars[d]).grid(row=row, column=col, sticky='w', padx=10, pady=2)
        
        # NACC Calendars
        nacc_frame = ctk.CTkFrame(schedule_frame)
        nacc_frame.pack(fill='x', padx=10, pady=5)
        ctk.CTkCheckBox(nacc_frame, text='NACC Calendars', 
                       variable=sched_vars['NACC Calendars'],
                       font=ctk.CTkFont(weight="bold")).pack(anchor='w', padx=10, pady=8)
        
        # Youth Schedules
        youth_opts = ['Kitchener District', 'Hamilton District']
        youth_vars = {d: ctk.IntVar(value=1 if d in (saved['schedules_sub'].get('Youth Schedules') or []) else 0) for d in youth_opts}
        
        youth_frame = ctk.CTkFrame(schedule_frame)
        youth_frame.pack(fill='x', padx=10, pady=5)
        ctk.CTkCheckBox(youth_frame, text='Youth Schedules', 
                       variable=sched_vars['Youth Schedules'],
                       font=ctk.CTkFont(weight="bold")).pack(anchor='w', padx=10, pady=5)
        youth_sub_frame = ctk.CTkFrame(youth_frame, fg_color="transparent")
        youth_sub_frame.pack(fill='x', padx=30, pady=(0, 5))
        for d in youth_opts:
            ctk.CTkCheckBox(youth_sub_frame, text=d, variable=youth_vars[d]).pack(anchor='w', padx=10, pady=2)
        
        # Seniors Schedules
        seniors_opts = ['Tri-District', 'Margaret Ave']
        seniors_vars = {d: ctk.IntVar(value=1 if d in (saved['schedules_sub'].get('Seniors Schedules') or []) else 0) for d in seniors_opts}
        
        seniors_frame = ctk.CTkFrame(schedule_frame)
        seniors_frame.pack(fill='x', padx=10, pady=5)
        ctk.CTkCheckBox(seniors_frame, text='Seniors Schedules', 
                       variable=sched_vars['Seniors Schedules'],
                       font=ctk.CTkFont(weight="bold")).pack(anchor='w', padx=10, pady=5)
        seniors_sub_frame = ctk.CTkFrame(seniors_frame, fg_color="transparent")
        seniors_sub_frame.pack(fill='x', padx=30, pady=(0, 5))
        for d in seniors_opts:
            ctk.CTkCheckBox(seniors_sub_frame, text=d, variable=seniors_vars[d]).pack(anchor='w', padx=10, pady=2)
        
        # ===== SECTION 2: Content Types =====
        content_frame = ctk.CTkFrame(scrollable_download)
        content_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(content_frame, text='📄 Content to Extract', 
                    font=ctk.CTkFont(size=15, weight="bold")).pack(anchor='w', padx=15, pady=(15, 10))
        
        options = ['English', 'French', 'Audio', 'Transcript', 'Bible Reading', 'Foreword', 'Full DSG', 'Bible References', 'Special Edition DSG']
        opt_vars = {o: ctk.IntVar(value=1 if o in saved['selections'] else 0) for o in options}
        
        content_grid = ctk.CTkFrame(content_frame, fg_color="transparent")
        content_grid.pack(fill='x', padx=20, pady=(0, 10))
        for i, o in enumerate(options):
            col = i % 3
            row = i // 3
            ctk.CTkCheckBox(content_grid, text=o, variable=opt_vars[o]).grid(row=row, column=col, sticky='w', padx=15, pady=3)
        
        # ===== SECTION 3: Languages =====
        lang_frame = ctk.CTkFrame(scrollable_download)
        lang_frame.pack(fill='x', padx=10, pady=5)
        
        ctk.CTkLabel(lang_frame, text='🌐 Language Preferences', 
                    font=ctk.CTkFont(size=15, weight="bold")).pack(anchor='w', padx=15, pady=(15, 10))
        
        lang_options = ['English', 'French', 'German', 'Italian', 'Portuguese', 'Russian', 'Spanish']
        full_lang_vars = {l: ctk.IntVar(value=1 if l in saved['full_dsg_langs'] else 0) for l in lang_options}
        se_lang_vars = {l: ctk.IntVar(value=1 if l in saved['se_dsg_langs'] else 0) for l in lang_options}
        foreword_lang_vars = {l: ctk.IntVar(value=1 if l in saved['foreword_langs'] else 0) for l in ['English', 'French']}
        bibread_lang_vars = {l: ctk.IntVar(value=1 if l in saved['bible_reading_langs'] else 0) for l in ['English', 'French']}
        bibref_lang_vars = {l: ctk.IntVar(value=1 if l in saved['bible_references_langs'] else 0) for l in ['English', 'French']}
        
        # Full DSG Languages
        full_dsg_subframe = ctk.CTkFrame(lang_frame)
        full_dsg_subframe.pack(fill='x', padx=20, pady=5)
        ctk.CTkLabel(full_dsg_subframe, text='Full DSG:', font=ctk.CTkFont(weight="bold")).pack(anchor='w', padx=10, pady=(8,5))
        full_grid = ctk.CTkFrame(full_dsg_subframe, fg_color="transparent")
        full_grid.pack(fill='x', padx=20, pady=(0, 8))
        for i, l in enumerate(lang_options):
            col = i % 4
            row = i // 4
            ctk.CTkCheckBox(full_grid, text=l, variable=full_lang_vars[l]).grid(row=row, column=col, sticky='w', padx=10, pady=2)
        
        # Special Edition DSG Languages
        se_dsg_subframe = ctk.CTkFrame(lang_frame)
        se_dsg_subframe.pack(fill='x', padx=20, pady=5)
        ctk.CTkLabel(se_dsg_subframe, text='Special Edition DSG:', font=ctk.CTkFont(weight="bold")).pack(anchor='w', padx=10, pady=(8,5))
        se_grid = ctk.CTkFrame(se_dsg_subframe, fg_color="transparent")
        se_grid.pack(fill='x', padx=20, pady=(0, 8))
        for i, l in enumerate(lang_options):
            col = i % 4
            row = i // 4
            ctk.CTkCheckBox(se_grid, text=l, variable=se_lang_vars[l]).grid(row=row, column=col, sticky='w', padx=10, pady=2)
        
        # Other language options (2-column layout for English/French only)
        other_lang_frame = ctk.CTkFrame(lang_frame, fg_color="transparent")
        other_lang_frame.pack(fill='x', padx=20, pady=5)
        
        # Foreword
        foreword_subframe = ctk.CTkFrame(other_lang_frame)
        foreword_subframe.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        ctk.CTkLabel(foreword_subframe, text='Foreword:', font=ctk.CTkFont(weight="bold")).pack(anchor='w', padx=10, pady=(8,5))
        for l in ['English', 'French']:
            ctk.CTkCheckBox(foreword_subframe, text=l, variable=foreword_lang_vars[l]).pack(anchor='w', padx=20, pady=2)
        
        # Bible Reading
        bibread_subframe = ctk.CTkFrame(other_lang_frame)
        bibread_subframe.grid(row=0, column=1, sticky='ew', padx=5, pady=5)
        ctk.CTkLabel(bibread_subframe, text='Bible Reading:', font=ctk.CTkFont(weight="bold")).pack(anchor='w', padx=10, pady=(8,5))
        for l in ['English', 'French']:
            ctk.CTkCheckBox(bibread_subframe, text=l, variable=bibread_lang_vars[l]).pack(anchor='w', padx=20, pady=2)
        
        # Bible References
        bibref_subframe = ctk.CTkFrame(other_lang_frame)
        bibref_subframe.grid(row=0, column=2, sticky='ew', padx=5, pady=5)
        ctk.CTkLabel(bibref_subframe, text='Bible References:', font=ctk.CTkFont(weight="bold")).pack(anchor='w', padx=10, pady=(8,5))
        for l in ['English', 'French']:
            ctk.CTkCheckBox(bibref_subframe, text=l, variable=bibref_lang_vars[l]).pack(anchor='w', padx=20, pady=2)
        
        other_lang_frame.grid_columnconfigure(0, weight=1)
        other_lang_frame.grid_columnconfigure(1, weight=1)
        other_lang_frame.grid_columnconfigure(2, weight=1)
        
        # ===== SECTION 4: Settings =====
        settings_frame = ctk.CTkFrame(scrollable_download)
        settings_frame.pack(fill='x', padx=10, pady=(5, 15))
        
        ctk.CTkLabel(settings_frame, text='⚙️ Settings', 
                    font=ctk.CTkFont(size=15, weight="bold")).pack(anchor='w', padx=15, pady=(15, 10))
        
        auto_submit_var = ctk.IntVar(value=1 if saved.get('auto_submit_enabled', True) else 0)
        ctk.CTkCheckBox(settings_frame, text='Enable auto-submit (5s countdown)', 
                       variable=auto_submit_var).pack(anchor='w', padx=20, pady=8)

        # ===== TAB 2: Month Selection =====
        tabview.add("Month Selection")
        tab_months = tabview.tab("Month Selection")
        
        months = ['January', 'February', 'March', 'April', 'May', 'June', 
                  'July', 'August', 'September', 'October', 'November', 'December']
        month_vars = {m: ctk.IntVar(value=1 if m in saved['selected_months'] else 0) for m in months}
        ctk.CTkLabel(tab_months, text='Select months to download:', font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, columnspan=2, sticky='w', pady=(10, 10), padx=10)
        
        # First column of months (Jan-Jun)
        for i, m in enumerate(months[:6], start=1):
            ctk.CTkCheckBox(tab_months, text=m, variable=month_vars[m]).grid(row=i, column=0, sticky='w', padx=20, pady=3)
        # Second column of months (Jul-Dec)
        for i, m in enumerate(months[6:], start=1):
            ctk.CTkCheckBox(tab_months, text=m, variable=month_vars[m]).grid(row=i, column=1, sticky='w', padx=20, pady=3)
        
        # Select/Deselect All buttons
        month_btn_frame = ctk.CTkFrame(tab_months, fg_color="transparent")
        month_btn_frame.grid(row=7, column=0, columnspan=2, pady=(15, 0))
        
        def select_all_months():
            for v in month_vars.values():
                v.set(1)
        
        def deselect_all_months():
            for v in month_vars.values():
                v.set(0)
        
        ctk.CTkButton(month_btn_frame, text='Select All', command=select_all_months, width=120).grid(row=0, column=0, padx=5)
        ctk.CTkButton(month_btn_frame, text='Deselect All', command=deselect_all_months, width=120).grid(row=0, column=1, padx=5)
        
        # Year Selection
        ctk.CTkLabel(tab_months, text='Select years:', font=ctk.CTkFont(size=14, weight="bold")).grid(row=8, column=0, columnspan=2, sticky='w', pady=(20, 10), padx=10)
        
        # Generate year range (current year - 1 to current year + 1)
        from datetime import datetime
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year - 1, current_year + 2)]
        year_vars = {y: ctk.IntVar(value=1 if y in saved['selected_years'] else 0) for y in years}
        
        year_frame = ctk.CTkFrame(tab_months, fg_color="transparent")
        year_frame.grid(row=9, column=0, columnspan=2, sticky='w', padx=20)
        
        for i, y in enumerate(years):
            ctk.CTkCheckBox(year_frame, text=y, variable=year_vars[y]).grid(row=0, column=i, sticky='w', padx=10, pady=3)
        
        # ===== TAB 3: PDF Highlighting =====
        tabview.add("PDF Highlighting")
        tab_highlight = tabview.tab("PDF Highlighting")
        
        # Load highlighting settings
        try:
            from src.pdf_highlighter import load_highlight_settings, save_highlight_settings
            highlight_settings = load_highlight_settings()
        except Exception:
            highlight_settings = {
                "names": [],
                "settings": {
                    "auto_highlight_on_download": True,
                    "create_copy": False,
                    "highlight_opacity": 0.5
                }
            }
        
        ctk.CTkLabel(tab_highlight, text='Names to Highlight in Schedules:', font=ctk.CTkFont(size=14, weight="bold")).pack(anchor='w', pady=(10, 10), padx=10)
        
        # Store name entries
        name_entries = list(highlight_settings.get('names', []))
        
        # Define opacity variable early (needed for preview updates)
        auto_highlight_var = ctk.IntVar(value=1 if highlight_settings.get('settings', {}).get('auto_highlight_on_download', True) else 0)
        create_copy_var = ctk.IntVar(value=1 if highlight_settings.get('settings', {}).get('create_copy', False) else 0)
        opacity_var = ctk.DoubleVar(value=highlight_settings.get('settings', {}).get('highlight_opacity', 0.5))
        
        # Container for name rows with scrollbar
        container_frame = ctk.CTkFrame(tab_highlight)
        container_frame.pack(fill='both', expand=True, pady=(0, 10), padx=10)
        
        # Scrollable frame for names
        scrollable_frame = ctk.CTkScrollableFrame(container_frame, height=250)
        scrollable_frame.pack(fill='both', expand=True)
        
        # Store row widgets for refresh
        name_row_widgets = []
        
        def hex_to_rgba(hex_color, opacity=0.5):
            """Convert hex to rgba for preview background"""
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            # Calculate lighter background for preview
            alpha = opacity
            bg_r = int(255 * (1 - alpha) + r * alpha)
            bg_g = int(255 * (1 - alpha) + g * alpha)
            bg_b = int(255 * (1 - alpha) + b * alpha)
            return f'#{bg_r:02x}{bg_g:02x}{bg_b:02x}'
        
        def create_name_row(idx, entry):
            """Create an inline editable row for a name entry"""
            row_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
            row_frame.pack(fill='x', pady=4, padx=5)
            
            # Enable/Disable checkbox
            enabled_var = ctk.IntVar(value=1 if entry.get('enabled', True) else 0)
            def toggle_enabled():
                entry['enabled'] = bool(enabled_var.get())
            
            cb = ctk.CTkCheckBox(row_frame, text="", variable=enabled_var, command=toggle_enabled, width=30)
            cb.pack(side='left', padx=(0, 5))
            
            # Name entry field
            name_var = ctk.StringVar(value=entry.get('name', ''))
            name_entry_widget = ctk.CTkEntry(row_frame, textvariable=name_var, width=180)
            name_entry_widget.pack(side='left', padx=5)
            
            def update_name(*args):
                entry['name'] = name_var.get()
                update_preview()
            name_var.trace('w', update_name)
            
            # Preview label with highlight color
            preview_label = ctk.CTkLabel(row_frame, text='', width=180, anchor='w', corner_radius=5)
            preview_label.pack(side='left', padx=5)
            
            def update_preview():
                preview_text = name_var.get() or 'Preview'
                bg_color = hex_to_rgba(entry.get('color', '#FFFF00'), opacity_var.get())
                preview_label.configure(text=preview_text, fg_color=bg_color, text_color="black")
            
            # Color picker button
            def pick_color():
                color = colorchooser.askcolor(title='Choose highlight color', initialcolor=entry.get('color', '#FFFF00'))
                if color[1]:
                    entry['color'] = color[1]
                    update_preview()
            
            color_btn = ctk.CTkButton(row_frame, text='🎨', width=40, command=pick_color)
            color_btn.pack(side='left', padx=2)
            
            # Delete button
            def delete_row():
                if idx < len(name_entries):
                    del name_entries[idx]
                    refresh_all_rows()
            
            del_btn = ctk.CTkButton(row_frame, text='×', width=40, command=delete_row, fg_color="red", hover_color="darkred")
            del_btn.pack(side='left', padx=2)
            
            update_preview()
            return row_frame
        
        def refresh_all_rows():
            """Clear and recreate all name rows"""
            for widget in scrollable_frame.winfo_children():
                widget.destroy()
            
            for idx, entry in enumerate(name_entries):
                create_name_row(idx, entry)
        
        # Initial population
        refresh_all_rows()
        
        # Add new name button
        def add_new_name():
            name_entries.append({
                'name': 'New Name',
                'color': '#FFFF00',
                'enabled': True
            })
            refresh_all_rows()
        
        btn_add_frame = ctk.CTkFrame(tab_highlight, fg_color="transparent")
        btn_add_frame.pack(fill='x', pady=(0, 10), padx=10)
        ctk.CTkButton(btn_add_frame, text='+ Add Name', command=add_new_name, width=150).pack(side='left')
        
        # Settings
        ctk.CTkLabel(tab_highlight, text='Highlighting Settings:', font=ctk.CTkFont(size=13, weight="bold")).pack(anchor='w', pady=(15, 10), padx=10)
        
        # Update all previews when opacity changes
        def update_all_previews(*args):
            refresh_all_rows()
        opacity_var.trace('w', update_all_previews)
        
        ctk.CTkCheckBox(tab_highlight, text='Auto-highlight schedules after download', variable=auto_highlight_var).pack(anchor='w', pady=3, padx=10)
        ctk.CTkCheckBox(tab_highlight, text='Create highlighted copy (preserve original)', variable=create_copy_var).pack(anchor='w', pady=3, padx=10)
        
        opacity_frame = ctk.CTkFrame(tab_highlight, fg_color="transparent")
        opacity_frame.pack(fill='x', pady=10, padx=10)
        ctk.CTkLabel(opacity_frame, text='Highlight opacity:').pack(side='left', padx=(0, 10))
        opacity_scale = ctk.CTkSlider(opacity_frame, from_=0.1, to=1.0, variable=opacity_var, width=200)
        opacity_scale.pack(side='left')
        opacity_label = ctk.CTkLabel(opacity_frame, text=f'{opacity_var.get():.1f}')
        opacity_label.pack(side='left', padx=10)
        
        def update_opacity_label(*args):
            opacity_label.configure(text=f'{opacity_var.get():.1f}')
        opacity_var.trace('w', update_opacity_label)
        
        def apply_to_existing():
            # Import CTkMessagebox once, outside try-except
            try:
                from CTkMessagebox import CTkMessagebox
                use_ctk_messagebox = True
            except:
                import tkinter.messagebox as messagebox
                use_ctk_messagebox = False
            
            try:
                from src.pdf_highlighter import process_schedule_pdfs
                from src.actions import find_schedule_pdfs
                from src.config import DSGS_DIR
                
                # Save current settings first
                current_settings = {
                    'names': name_entries,
                    'settings': {
                        'auto_highlight_on_download': bool(auto_highlight_var.get()),
                        'create_copy': bool(create_copy_var.get()),
                        'highlight_opacity': opacity_var.get()
                    }
                }
                save_highlight_settings(current_settings)
                
                # Find and process PDFs
                all_pdfs = find_schedule_pdfs(DSGS_DIR)
                
                # Check if create_copy is enabled - if so, only process originals
                create_copy_enabled = current_settings.get('settings', {}).get('create_copy', False)
                
                # Filter PDFs based on selected months and years
                selected_months = {m for m, v in month_vars.items() if v.get()}
                selected_years = {y for y, v in year_vars.items() if v.get()}
                
                pdfs = []
                for pdf in all_pdfs:
                    filename = os.path.basename(pdf)
                    path = pdf.replace(DSGS_DIR, '').replace('\\', '/')
                    
                    # If create_copy is enabled, skip already-highlighted files
                    if create_copy_enabled and ' - Highlighted' in filename:
                        continue
                    
                    # Check month filter
                    month_match = not selected_months or any(month.lower() in filename.lower() for month in selected_months)
                    
                    # Check year filter (look in both filename and path)
                    year_match = not selected_years or any(year in path or year in filename for year in selected_years)
                    
                    if month_match and year_match:
                        pdfs.append(pdf)
                
                if not pdfs:
                    if use_ctk_messagebox:
                        CTkMessagebox(title='No PDFs Found', message='No schedule PDFs found to highlight for the selected months.', icon="info")
                    else:
                        messagebox.showinfo('No PDFs Found', 'No schedule PDFs found to highlight for the selected months.')
                    return
                
                # Create formatted list of PDF files
                pdf_list = '\n'.join([f"• {os.path.basename(pdf)}" for pdf in pdfs])
                confirm_msg = f"Found {len(pdfs)} schedule PDF(s):\n\n{pdf_list}\n\nApply highlighting to all?"
                
                if use_ctk_messagebox:
                    msg = CTkMessagebox(title='Apply Highlighting', 
                        message=confirm_msg,
                        icon="question", option_1="No", option_2="Yes")
                    proceed = msg.get() == "Yes"
                else:
                    proceed = messagebox.askyesno('Apply Highlighting', confirm_msg)
                
                if proceed:
                    results = process_schedule_pdfs(pdfs, current_settings)
                    total = sum(sum(counts.values()) for counts in results.values())
                    if use_ctk_messagebox:
                        CTkMessagebox(title='Complete', message=f'Added {total} highlights to {len(results)} PDF(s).', icon="check")
                    else:
                        messagebox.showinfo('Complete', f'Added {total} highlights to {len(results)} PDF(s).')
            except Exception as e:
                # Show error using appropriate messagebox
                if use_ctk_messagebox:
                    CTkMessagebox(title='Error', message=f'Error applying highlights: {e}', icon="cancel")
                else:
                    messagebox.showerror('Error', f'Error applying highlights: {e}')
        
        def clear_existing_highlights():
            # Import CTkMessagebox once, outside try-except
            try:
                from CTkMessagebox import CTkMessagebox
                use_ctk_messagebox = True
            except:
                import tkinter.messagebox as messagebox
                use_ctk_messagebox = False
            
            try:
                from src.pdf_highlighter import clear_highlights_from_pdfs, load_highlight_settings
                from src.actions import find_schedule_pdfs
                from src.config import DSGS_DIR
                
                # Load settings to check create_copy option
                highlight_settings = load_highlight_settings()
                
                # Check if create_copy is enabled - if so, only clear highlighted copies
                create_copy = highlight_settings.get('settings', {}).get('create_copy', False)
                
                # Find PDFs
                all_pdfs = find_schedule_pdfs(DSGS_DIR)
                
                # Filter PDFs based on selected months and years
                selected_months = {m for m, v in month_vars.items() if v.get()}
                selected_years = {y for y, v in year_vars.items() if v.get()}
                
                pdfs = []
                for pdf in all_pdfs:
                    filename = os.path.basename(pdf)
                    path = pdf.replace(DSGS_DIR, '').replace('\\', '/')
                    
                    # If create_copy is enabled, only include highlighted copies
                    if create_copy and ' - Highlighted' not in filename:
                        continue
                    
                    # Check month filter
                    month_match = not selected_months or any(month.lower() in filename.lower() for month in selected_months)
                    
                    # Check year filter (look in both filename and path)
                    year_match = not selected_years or any(year in path or year in filename for year in selected_years)
                    
                    if month_match and year_match:
                        pdfs.append(pdf)
                
                if not pdfs:
                    if use_ctk_messagebox:
                        CTkMessagebox(title='No PDFs Found', message='No schedule PDFs found for the selected months.', icon="info")
                    else:
                        messagebox.showinfo('No PDFs Found', 'No schedule PDFs found for the selected months.')
                    return
                
                # Create formatted list of PDF files
                pdf_list = '\n'.join([f"• {os.path.basename(pdf)}" for pdf in pdfs])
                
                if create_copy:
                    # If create_copy is enabled, we'll clear highlights from the highlighted copies
                    confirm_msg = f"Found {len(pdfs)} highlighted copy/copies:\n\n{pdf_list}\n\nClear all highlights and background colors from these copies?"
                else:
                    # Otherwise, clear highlights from the PDFs
                    confirm_msg = f"Found {len(pdfs)} schedule PDF(s):\n\n{pdf_list}\n\nClear all highlights and background colors from these PDFs?"
                
                if use_ctk_messagebox:
                    msg = CTkMessagebox(title='Clear Highlights', 
                        message=confirm_msg,
                        icon="warning", option_1="No", option_2="Yes")
                    proceed = msg.get() == "Yes"
                else:
                    proceed = messagebox.askyesno('Clear Highlights', confirm_msg)
                
                if proceed:
                    # Clear highlights (and background colors) from PDFs
                    results = clear_highlights_from_pdfs(pdfs)
                    total = sum(results.values())
                    if use_ctk_messagebox:
                        CTkMessagebox(title='Complete', message=f'Cleared {total} highlight(s) and background colors from {len(results)} PDF(s).', icon="check")
                    else:
                        messagebox.showinfo('Complete', f'Cleared {total} highlight(s) and background colors from {len(results)} PDF(s).')
            except Exception as e:
                # Show error using appropriate messagebox
                if use_ctk_messagebox:
                    CTkMessagebox(title='Error', message=f'Error clearing highlights: {e}', icon="cancel")
                else:
                    messagebox.showerror('Error', f'Error clearing highlights: {e}')
        
        ctk.CTkButton(tab_highlight, text='Apply to Existing PDFs', command=apply_to_existing, width=200).pack(pady=15, padx=10)
        ctk.CTkButton(tab_highlight, text='Clear All Highlights', command=clear_existing_highlights, width=200).pack(pady=5, padx=10)

        result: Dict[str, Any] = {}

        def save_all_settings():
            """Save all settings to .env and JSON files without submitting"""
            # Save download settings to .env
            chosen_sched = {s for s, v in sched_vars.items() if v.get()}
            schedules_sub: Dict[str, Set[str]] = {}
            if any(v.get() for v in district_vars.values()):
                schedules_sub['District Serving Schedules'] = {d for d, v in district_vars.items() if v.get()}
            if any(v.get() for v in youth_vars.values()):
                schedules_sub['Youth Schedules'] = {d for d, v in youth_vars.items() if v.get()}
            if any(v.get() for v in seniors_vars.values()):
                schedules_sub['Seniors Schedules'] = {d for d, v in seniors_vars.items() if v.get()}
            if 'NACC Calendars' in chosen_sched and 'NACC Calendars' not in schedules_sub:
                schedules_sub['NACC Calendars'] = set()

            selections_set = {o for o, v in opt_vars.items() if v.get()}
            selected_months = {m for m, v in month_vars.items() if v.get()}
            selected_years = {y for y, v in year_vars.items() if v.get()}
            
            _save_json_env('DSG_UI_SELECTIONS', selections_set)
            _save_json_env('DSG_UI_SCHEDULES_CHOSEN', chosen_sched)
            _save_json_env('DSG_UI_SCHEDULES_SUB', schedules_sub)
            _save_json_env('DSG_UI_FULL_DSG_LANGS', {l for l, v in full_lang_vars.items() if v.get()})
            _save_json_env('DSG_UI_SE_DSG_LANGS', {l for l, v in se_lang_vars.items() if v.get()})
            _save_json_env('DSG_UI_BIBLE_READING_LANGS', {l for l, v in bibread_lang_vars.items() if v.get()})
            _save_json_env('DSG_UI_FOREWORD_LANGS', {l for l, v in foreword_lang_vars.items() if v.get()})
            _save_json_env('DSG_UI_BIBLE_REFERENCES_LANGS', {l for l, v in bibref_lang_vars.items() if v.get()})
            _save_json_env('DSG_UI_AUTO_SUBMIT', bool(auto_submit_var.get()))
            _save_json_env('DSG_UI_SELECTED_MONTHS', selected_months)
            _save_json_env('DSG_UI_SELECTED_YEARS', selected_years)
            
            # Save highlighting settings
            try:
                from src.pdf_highlighter import save_highlight_settings
                highlight_config = {
                    'names': name_entries,
                    'settings': {
                        'auto_highlight_on_download': bool(auto_highlight_var.get()),
                        'create_copy': bool(create_copy_var.get()),
                        'highlight_opacity': opacity_var.get()
                    }
                }
                save_highlight_settings(highlight_config)
            except Exception:
                pass

        def on_save():
            """Save settings without submitting"""
            save_all_settings()
            import tkinter.messagebox as messagebox
            messagebox.showinfo('Settings Saved', 'All settings have been saved successfully.')

        def on_submit():
            """Save settings and submit to run the download"""
            save_all_settings()
            
            # Populate result for download execution
            chosen_sched = {s for s, v in sched_vars.items() if v.get()}
            schedules_sub: Dict[str, Set[str]] = {}
            if any(v.get() for v in district_vars.values()):
                schedules_sub['District Serving Schedules'] = {d for d, v in district_vars.items() if v.get()}
            if any(v.get() for v in youth_vars.values()):
                schedules_sub['Youth Schedules'] = {d for d, v in youth_vars.items() if v.get()}
            if any(v.get() for v in seniors_vars.values()):
                schedules_sub['Seniors Schedules'] = {d for d, v in seniors_vars.items() if v.get()}
            if 'NACC Calendars' in chosen_sched and 'NACC Calendars' not in schedules_sub:
                schedules_sub['NACC Calendars'] = set()

            selections_set = {o for o, v in opt_vars.items() if v.get()}
            selected_months = {m for m, v in month_vars.items() if v.get()}
            selected_years = {y for y, v in year_vars.items() if v.get()}
            
            result.update({
                'schedules_chosen': chosen_sched,
                'schedules_sub': schedules_sub,
                'selections': selections_set,
                'full_dsg_langs': {l for l, v in full_lang_vars.items() if v.get()},
                'se_dsg_langs': {l for l, v in se_lang_vars.items() if v.get()},
                'foreword_langs': {l for l, v in foreword_lang_vars.items() if v.get()},
                'bible_reading_langs': {l for l, v in bibread_lang_vars.items() if v.get()},
                'bible_references_langs': {l for l, v in bibref_lang_vars.items() if v.get()},
                'selected_months': selected_months,
                'selected_years': selected_years,
            })
            root.destroy()

        # Check if this is the first time the app is running by seeing if any saved data exists
        is_first_run = not any([
            saved.get('selections'),
            saved.get('schedules_chosen'),
            saved.get('schedules_sub')
        ])

        remaining_seconds = ctk.IntVar(value=5)

        # Only start the countdown if it is NOT the first run AND auto-submit is enabled
        if not is_first_run and auto_submit_var.get():
            countdown_var = ctk.StringVar(value=f"Auto-submit in {remaining_seconds.get()}s")
            countdown_label = ctk.CTkLabel(root, textvariable=countdown_var, 
                                          font=ctk.CTkFont(size=13, weight="bold"),
                                          text_color="orange")
            countdown_label.pack(pady=(10, 0))

            def _update_countdown_label():
                countdown_var.set(f"Auto-submit in {remaining_seconds.get()}s")

            def reset_countdown(*_):
                remaining_seconds.set(5)
                _update_countdown_label()

            def tick():
                remaining_seconds.set(max(0, remaining_seconds.get() - 1))
                _update_countdown_label()
                if remaining_seconds.get() <= 0:
                    try:
                        on_submit()
                    except Exception:
                        pass
                else:
                    root.after(1000, tick)

            # Start the 5-second tick
            root.after(1000, tick)
        else:
            # First-time users see a manual prompt message instead
            status_label = ctk.CTkLabel(root, text="Configure your options and click Submit when ready.", 
                                       font=ctk.CTkFont(size=12))
            status_label.pack(pady=(10, 0))

        # attach traces to all IntVars to reset the countdown if a user interacts
        all_vars = list(sched_vars.values()) + list(district_vars.values()) + \
                   list(youth_vars.values()) + list(seniors_vars.values()) + \
                   list(opt_vars.values()) + list(full_lang_vars.values()) + \
                   list(se_lang_vars.values()) + list(foreword_lang_vars.values()) + \
                   list(bibread_lang_vars.values()) + list(bibref_lang_vars.values()) + \
                   list(month_vars.values())
        
        for v in all_vars:
            try:
                # If it's the first run, we don't need reset_countdown because the timer isn't running
                if not is_first_run and auto_submit_var.get():
                    v.trace_add('write', lambda *a, v=v: reset_countdown())
            except Exception:
                pass

        def on_cancel():
            nonlocal cancelled
            cancelled = True
            root.destroy()

        # Handle window close button (X) same as Cancel
        root.protocol("WM_DELETE_WINDOW", on_cancel)

        # Bottom buttons
        btn_frame_bottom = ctk.CTkFrame(root, fg_color="transparent")
        btn_frame_bottom.pack(side='bottom', pady=15, padx=10)
        ctk.CTkButton(btn_frame_bottom, text='Submit', command=on_submit, width=120, height=35).grid(row=0, column=0, padx=8)
        ctk.CTkButton(btn_frame_bottom, text='Save', command=on_save, width=120, height=35, 
                     fg_color="gray40", hover_color="gray50").grid(row=0, column=1, padx=8)
        ctk.CTkButton(btn_frame_bottom, text='Cancel', command=on_cancel, width=120, height=35,
                     fg_color="gray40", hover_color="gray50").grid(row=0, column=2, padx=8)

        root.mainloop()

        # If user cancelled, return None to exit completely
        if cancelled:
            return None

        # If user submitted, return result (settings already saved)
        if result:
            return result
            
        # If window was closed without submit/cancel, return None
        return None
    except Exception:
        # GUI unavailable or failed; fall back to terminal
        pass

    # Terminal fallback
    schedule_options = [
        "District Serving Schedules",
        "NACC Calendars",
        "Youth Schedules",
        "Seniors Schedules",
    ]
    schedules_chosen = prompt_multichoice("Which schedule groups would you like to include?", schedule_options, defaults=saved['schedules_chosen'])

    schedules_sub: Dict[str, Set[str]] = {}
    if 'District Serving Schedules' in schedules_chosen:
        districts = ['British Columbia', 'Alberta', 'Saskatchewan', 'Manitoba', 'Northern Ontario', 'Kitchener', 'Hamilton', 'Toronto', 'Eastern Canada']
        sel = prompt_multichoice("Which district serving schedules? (multiple OK)", districts, defaults=saved['schedules_sub'].get('District Serving Schedules'))
        schedules_sub['District Serving Schedules'] = sel

    if 'NACC Calendars' in schedules_chosen:
        nacc_opts = ['National', 'Districts']
        sel = prompt_multichoice("Which NACC Calendars?", nacc_opts, defaults=saved['schedules_sub'].get('NACC Calendars'))
        schedules_sub['NACC Calendars'] = sel

    if 'Youth Schedules' in schedules_chosen:
        youth_opts = ['Kitchener District', 'Hamilton District']
        sel = prompt_multichoice("Which Youth schedules?", youth_opts, defaults=saved['schedules_sub'].get('Youth Schedules'))
        schedules_sub['Youth Schedules'] = sel

    if 'Seniors Schedules' in schedules_chosen:
        seniors_opts = ['Tri-District', 'Margaret Ave']
        sel = prompt_multichoice("Which Seniors schedules?", seniors_opts, defaults=saved['schedules_sub'].get('Seniors Schedules'))
        schedules_sub['Seniors Schedules'] = sel

    options = [
        "English",
        "French",
        "Audio",
        "Transcript",
        "Bible Reading",
        "Foreword",
        "Full DSG",
        "Bible References",
        "Special Edition DSG",
    ]

    selections = prompt_multichoice("Which items would you like to extract?", options, defaults=saved['selections'])

    bible_reading_langs = set()
    if "Bible Reading" in selections:
        bible_reading_langs = prompt_languages("Bible Reading languages (choose any):", ["English", "French"], defaults=saved['bible_reading_langs']) or {"English", "French"}

    lang_options = ["English", "French", "German", "Italian", "Portuguese", "Russian", "Spanish"]
    full_dsg_langs = set()
    se_dsg_langs = set()
    foreword_langs = set()
    bible_references_langs = set()
    if "Full DSG" in selections:
        full_dsg_langs = prompt_languages("Full DSG languages (choose any):", lang_options, defaults=saved['full_dsg_langs'])
    if "Special Edition DSG" in selections:
        se_dsg_langs = prompt_languages("Special Edition DSG languages (choose any):", lang_options, defaults=saved['se_dsg_langs'])
    if "Foreword" in selections:
        foreword_langs = prompt_languages("Foreword languages (choose any):", ["English", "French"], defaults=saved['foreword_langs']) or {"English", "French"}
    if "Bible References" in selections:
        bible_references_langs = prompt_languages("Bible References languages (choose any):", ["English", "French"], defaults=saved['bible_references_langs']) or {"English", "French"}

    # Month selection
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    selected_months = prompt_multichoice("Which months would you like to download?", months, defaults=saved.get('selected_months', months))

    sel_display: Dict[str, Any] = {
        'selections': selections,
        'bible_reading_langs': bible_reading_langs,
        'full_dsg_langs': full_dsg_langs,
        'se_dsg_langs': se_dsg_langs,
        'foreword_langs': foreword_langs,
        'bible_references_langs': bible_references_langs,
        'schedules_chosen': schedules_chosen,
        'schedules_sub': schedules_sub,
        'selected_months': selected_months,
    }

    # persist choices
    _save_json_env('DSG_UI_SELECTIONS', sel_display['selections'])
    _save_json_env('DSG_UI_SCHEDULES_CHOSEN', sel_display['schedules_chosen'])
    _save_json_env('DSG_UI_SCHEDULES_SUB', sel_display['schedules_sub'])
    _save_json_env('DSG_UI_FULL_DSG_LANGS', sel_display['full_dsg_langs'])
    _save_json_env('DSG_UI_SE_DSG_LANGS', sel_display['se_dsg_langs'])
    _save_json_env('DSG_UI_BIBLE_READING_LANGS', sel_display['bible_reading_langs'])
    _save_json_env('DSG_UI_FOREWORD_LANGS', sel_display['foreword_langs'])
    _save_json_env('DSG_UI_BIBLE_REFERENCES_LANGS', sel_display['bible_references_langs'])
    _save_json_env('DSG_UI_SELECTED_MONTHS', sel_display['selected_months'])

    print("\nUser has selected:")
    if selections:
        for s in sorted(selections):
            print(f"- {s}")
    else:
        print("- (none)")

    if schedules_chosen:
        print("Schedule groups selected:")
        for s in sorted(schedules_chosen):
            print(f"- {s}")
            subs = schedules_sub.get(s, schedules_sub.get(s.title(), set()))
            if subs:
                print("  choices:", ", ".join(sorted(subs)))

    return sel_display