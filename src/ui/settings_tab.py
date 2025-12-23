"""UI components for the Settings tab"""

import customtkinter as ctk
from tkinter import filedialog

def create_settings_tab(tab, saved_data):
    """Creates the Settings tab and its widgets."""
    tab.grid_columnconfigure(1, weight=1)
    
    ctk.CTkLabel(tab, text="Login Credentials", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="w")
    
    ctk.CTkLabel(tab, text="Username:").grid(row=1, column=0, padx=20, pady=5, sticky="w")
    username_entry = ctk.CTkEntry(tab)
    username_entry.grid(row=1, column=1, padx=20, pady=5, sticky="ew")
    username_entry.insert(0, saved_data["USERNAME"])

    ctk.CTkLabel(tab, text="Password:").grid(row=2, column=0, padx=20, pady=5, sticky="w")
    
    password_entry = ctk.CTkEntry(tab, show="*")
    password_entry.grid(row=2, column=1, padx=20, pady=5, sticky="ew")
    password_entry.insert(0, saved_data["PASSWORD"])

    def toggle_password_visibility():
        if password_entry.cget("show") == "*":
            password_entry.configure(show="")
            password_toggle_button.configure(text="Hide")
        else:
            password_entry.configure(show="*")
            password_toggle_button.configure(text="Show")

    password_toggle_button = ctk.CTkButton(tab, text="Show", width=80, command=toggle_password_visibility)
    password_toggle_button.grid(row=2, column=2, padx=10, pady=5)


    ctk.CTkLabel(tab, text="File Save Location", font=("Arial", 16, "bold")).grid(row=3, column=0, columnspan=2, padx=20, pady=(20, 5), sticky="w")
    ctk.CTkLabel(tab, text="This is where the downloaded files will be saved.").grid(row=4, column=0, columnspan=2, padx=20, pady=(0,10), sticky="w")

    ctk.CTkLabel(tab, text="Save Path:").grid(row=5, column=0, padx=20, pady=5, sticky="w")
    
    path_entry = ctk.CTkEntry(tab)
    path_entry.grid(row=5, column=1, sticky="ew", padx=20, pady=5)
    path_entry.insert(0, saved_data["DSGS_DIR"])

    def browse_path():
        directory = filedialog.askdirectory()
        if directory:
            path_entry.delete(0, "end")
            path_entry.insert(0, directory)

    browse_button = ctk.CTkButton(tab, text="Browse...", command=browse_path, width=80)
    browse_button.grid(row=5, column=2, padx=10, pady=5)

    ctk.CTkLabel(tab, text="Highlight Opacity", font=("Arial", 16, "bold")).grid(row=6, column=0, columnspan=2, padx=20, pady=(20, 5), sticky="w")
    
    opacity_slider = ctk.CTkSlider(tab, from_=0.1, to=1.0)
    opacity_slider.set(saved_data.get("HIGHLIGHT_OPACITY", 0.5))
    opacity_slider.grid(row=7, column=1, padx=20, pady=5, sticky="ew")
    
    opacity_label = ctk.CTkLabel(tab, text=f"{opacity_slider.get():.2f}")
    opacity_label.grid(row=7, column=2, padx=10, pady=5)

    def update_opacity_label(value):
        opacity_label.configure(text=f"{value:.2f}")

    opacity_slider.configure(command=update_opacity_label)


    return username_entry, password_entry, path_entry, opacity_slider
