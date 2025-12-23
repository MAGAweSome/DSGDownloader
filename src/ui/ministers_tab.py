"""UI components for the Ministers tab"""

from tkinter import colorchooser, messagebox
import customtkinter as ctk

def create_ministers_tab(tab, saved_data):
    """Creates the Ministers tab and its widgets."""
    current_ministers = saved_data["MINISTER_COLORS"]
    
    minister_frame_container = ctk.CTkFrame(tab)
    minister_frame_container.pack(padx=10, pady=10, fill="both", expand=True)
    ctk.CTkLabel(
        minister_frame_container, text="Minister Highlights", font=("Arial", 16, "bold")
    ).pack(pady=10)
    entry_frame = ctk.CTkFrame(minister_frame_container)
    entry_frame.pack(pady=5, padx=10, fill="x")
    name_entry = ctk.CTkEntry(
        entry_frame, placeholder_text="Enter Minister Name..."
    )
    name_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
    color_preview = ctk.CTkLabel(
        entry_frame, text="", width=40, height=28, corner_radius=6
    )
    color_preview.pack(side="left")

    selected_color = [1.0, 1.0, 0.0]
    editing_minister = None

    def pick_color():
        nonlocal selected_color
        color = colorchooser.askcolor(title="Choose Highlight Color")
        if color and color[1]:
            selected_color = [round(c / 255, 2) for c in color[0]]
            color_preview.configure(fg_color=color[1])

    def add_minister():
        name = name_entry.get().strip()
        if name and name != "Enter Minister Name...":
            current_ministers[name] = selected_color
            update_minister_list()
            name_entry.delete(0, "end")
        else:
            messagebox.showwarning("Input Error", "Please enter a valid minister name.")

    def edit_minister(name):
        nonlocal editing_minister, selected_color
        editing_minister = name
        name_entry.delete(0, "end")
        name_entry.insert(0, name)
        color_val = current_ministers[name]
        hex_color = f"#{int(color_val[0]*255):02x}{int(color_val[1]*255):02x}{int(color_val[2]*255):02x}"
        selected_color = color_val
        color_preview.configure(fg_color=hex_color)
        add_button.pack_forget()
        save_button.pack(side="left", padx=5)
        cancel_button.pack(side="left", padx=5)

    def save_minister():
        nonlocal editing_minister
        new_name = name_entry.get().strip()
        if not new_name:
            messagebox.showwarning("Input Error", "Minister name cannot be empty.")
            return
        if editing_minister and editing_minister != new_name:
            new_dict = {}
            for k, v in current_ministers.items():
                if k == editing_minister:
                    new_dict[new_name] = selected_color
                else:
                    new_dict[k] = v
            current_ministers.clear()
            current_ministers.update(new_dict)
        else:
            current_ministers[new_name] = selected_color
        cancel_edit()
        update_minister_list()

    def cancel_edit():
        nonlocal editing_minister
        editing_minister = None
        name_entry.delete(0, "end")
        save_button.pack_forget()
        cancel_button.pack_forget()
        add_button.pack(side="left", padx=5)
    
    def remove_minister(name_to_remove):
        if name_to_remove in current_ministers:
            del current_ministers[name_to_remove]
            update_minister_list()
    
    def move_minister(name: str, direction: int):
        names = list(current_ministers.keys())
        try:
            idx = names.index(name)
            new_idx = idx + direction
            if 0 <= new_idx < len(names):
                names.insert(new_idx, names.pop(idx))
                reordered_dict = {n: current_ministers[n] for n in names}
                current_ministers.clear()
                current_ministers.update(reordered_dict)
                update_minister_list()
        except ValueError:
            pass

    add_button = ctk.CTkButton(entry_frame, text="Add", command=add_minister)
    add_button.pack(side="left", padx=5)
    save_button = ctk.CTkButton(entry_frame, text="Save", command=save_minister)
    cancel_button = ctk.CTkButton(entry_frame, text="Cancel", command=cancel_edit)
    ctk.CTkButton(entry_frame, text="Pick Color", command=pick_color).pack(side="left", padx=10)

    minister_list_frame = ctk.CTkScrollableFrame(minister_frame_container)
    minister_list_frame.pack(pady=10, padx=10, fill="both", expand=True)

    def update_minister_list():
        for widget in minister_list_frame.winfo_children():
            widget.destroy()
        
        minister_names = list(current_ministers.keys())
        for i, name in enumerate(minister_names):
            color = current_ministers[name]
            frame = ctk.CTkFrame(minister_list_frame, corner_radius=6, fg_color="gray20")
            frame.pack(fill="x", pady=2, padx=5)

            hex_color = f"#{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}"
            ctk.CTkLabel(frame, text="", fg_color=hex_color, width=20, height=20, corner_radius=4).pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(frame, text=name, font=("Arial", 14)).pack(side="left", fill="x", expand=True, pady=5)
            
            down_button = ctk.CTkButton(frame, text="▼", width=30, command=lambda n=name: move_minister(n, 1))
            down_button.pack(side="right", pady=5)
            if i == len(minister_names) - 1:
                down_button.configure(state="disabled")

            up_button = ctk.CTkButton(frame, text="▲", width=30, command=lambda n=name: move_minister(n, -1))
            up_button.pack(side="right", padx=(0, 5), pady=5)
            if i == 0:
                up_button.configure(state="disabled")

            ctk.CTkButton(frame, text="Remove", width=60, command=lambda n=name: remove_minister(n)).pack(side="right", padx=5, pady=5)
            ctk.CTkButton(frame, text="Edit", width=60, command=lambda n=name: edit_minister(n)).pack(side="right", padx=5, pady=5)
    
    update_minister_list()

    return current_ministers