"""UI components for the DSG Prep tab"""

import customtkinter as ctk

def create_dsg_prep_tab(tab, saved_data):
    """Creates the DSG Prep tab and its widgets."""
    tab.grid_columnconfigure((0, 1), weight=1)
    prep_frame = ctk.CTkFrame(tab)
    prep_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    ctk.CTkLabel(
        prep_frame, text="Divine Service Prep", font=("Arial", 14, "bold")
    ).pack(pady=10)
    prep_options = ["English", "French", "Audio", "References", "Transcript"]
    prep_vars = {
        o: ctk.IntVar(value=1 if o in saved_data["selections"] else 0)
        for o in prep_options
    }
    for o in prep_options:
        ctk.CTkCheckBox(prep_frame, text=o, variable=prep_vars[o]).pack(
            anchor="w", padx=10, pady=5
        )

    bible_frame = ctk.CTkFrame(tab)
    bible_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    ctk.CTkLabel(
        bible_frame, text="Bible Readings", font=("Arial", 14, "bold")
    ).pack(pady=10)
    bible_options = ["English", "French"]
    bible_vars = {
        o: ctk.IntVar(value=1 if o in saved_data["bible_reading_langs"] else 0)
        for o in bible_options
    }
    for o in bible_options:
        ctk.CTkCheckBox(bible_frame, text=o, variable=bible_vars[o]).pack(
            anchor="w", padx=10, pady=5
        )
    
    return prep_vars, bible_vars
