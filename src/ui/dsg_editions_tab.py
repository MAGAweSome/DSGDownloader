"""UI components for the DSG Editions tab"""

import customtkinter as ctk

def create_dsg_editions_tab(tab, saved_data):
    """Creates the DSG Editions tab and its widgets."""
    tab.grid_columnconfigure((0, 1), weight=1)
    lang_options = [
        "English",
        "French",
        "German",
        "Italian",
        "Portuguese",
        "Russian",
        "Spanish",
    ]
    full_dsg_frame = ctk.CTkFrame(tab)
    full_dsg_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    ctk.CTkLabel(full_dsg_frame, text="Full DSG", font=("Arial", 14, "bold")).pack(
        pady=10
    )
    full_lang_vars = {
        l: ctk.IntVar(value=1 if l in saved_data["full_dsg_langs"] else 0)
        for l in lang_options
    }
    for l in lang_options:
        ctk.CTkCheckBox(full_dsg_frame, text=l, variable=full_lang_vars[l]).pack(
            anchor="w", padx=10, pady=5
        )

    se_dsg_frame = ctk.CTkFrame(tab)
    se_dsg_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    ctk.CTkLabel(
        se_dsg_frame, text="Special Edition DSG", font=("Arial", 14, "bold")
    ).pack(pady=10)
    se_lang_vars = {
        l: ctk.IntVar(value=1 if l in saved_data["se_dsg_langs"] else 0)
        for l in lang_options
    }
    for l in lang_options:
        ctk.CTkCheckBox(se_dsg_frame, text=l, variable=se_lang_vars[l]).pack(
            anchor="w", padx=10, pady=5
        )
    
    return full_lang_vars, se_lang_vars
