"""Modern, user-friendly UI for DSG Downloader with reordering buttons."""

from typing import Set, Iterable, Dict, Any
import os
import json
from tkinter import colorchooser, messagebox, filedialog
import customtkinter as ctk
from dotenv import set_key, get_key

ENV_PATH = os.path.join(os.getcwd(), ".env")

def prompt_multichoice(
    prompt: str, choices: Iterable[str], defaults: Iterable[str] | None = None
) -> Set[str]:
    """Displays a terminal prompt for multiple-choice selections."""
    # ... (implementation remains the same)
    return set()

def prompt_languages(
    prompt: str, langs: Iterable[str], defaults: Iterable[str] | None = None
) -> Set[str]:
    """Displays a terminal prompt for language selections."""
    return prompt_multichoice(prompt, list(langs), defaults=defaults)

def _load_json_env(key: str) -> Any:
    """Loads a JSON-encoded value from the .env file."""
    try:
        from dotenv import load_dotenv

        load_dotenv(ENV_PATH)
    except Exception:
        pass

    v = os.environ.get(key)
    if not v:
        return get_key(ENV_PATH, key)
    try:
        if key in ["USERNAME", "PASSWORD", "DSGS_DIR"]:
            return v
        return json.loads(v)
    except (json.JSONDecodeError, TypeError):
        return v


def _save_json_env(key: str, value: Any) -> None:
    """Saves a value as a JSON-encoded string to the .env file."""
    try:
        if key in ["USERNAME", "PASSWORD", "DSGS_DIR"]:
             set_key(ENV_PATH, key, value)
             return

        def _to_jsonable(v: Any) -> Any:
            """Recursively converts sets to lists for JSON serialization."""
            if isinstance(v, set):
                return list(v)
            if isinstance(v, dict):
                return {k: _to_jsonable(val) for k, val in v.items()}
            if isinstance(v, list):
                return [_to_jsonable(i) for i in v]
            return v

        serializable_value = _to_jsonable(value if value is not None else [])
        set_key(ENV_PATH, key, json.dumps(serializable_value))
    except Exception:
        pass


def get_user_selection() -> Dict[str, Any]:
    """Displays the GUI and returns user's choices with guided navigation."""
    saved_data = {
        "selections": set(_load_json_env("DSG_UI_SELECTIONS") or []),
        "schedules_chosen": set(_load_json_env("DSG_UI_SCHEDULES_CHOSEN") or []),
        "schedules_sub": _load_json_env("DSG_UI_SCHEDULES_SUB") or {},
        "full_dsg_langs": set(_load_json_env("DSG_UI_FULL_DSG_LANGS") or []),
        "se_dsg_langs": set(_load_json_env("DSG_UI_SE_DSG_LANGS") or []),
        "bible_reading_langs": set(_load_json_env("DSG_UI_BIBLE_READING_LANGS") or []),
        "USERNAME": _load_json_env("USERNAME") or "",
        "PASSWORD": _load_json_env("PASSWORD") or "",
        "DSGS_DIR": _load_json_env("DSGS_DIR") or "",
    }

    try:
        app = ctk.CTk()
        app.title("DSG Downloader - Options")
        app.geometry("800x700")

        editing_minister = None
        selected_color = [1.0, 1.0, 0.0]

        tab_names = ["DSG Prep", "DSG Editions", "Schedules", "Ministers", "Settings"]
        tab_view = ctk.CTkTabview(app, width=780)
        for name in tab_names:
            tab_view.add(name)
        tab_view.pack(padx=10, pady=10, fill="both", expand=True)
        
        visited_tabs = {tab_names[0]}

        def on_tab_change(): # No longer needs current_tab_name as argument
            current_tab = tab_view.get()
            visited_tabs.add(current_tab)
            
            if current_tab == tab_names[0]:
                back_button.pack_forget()
            else:
                back_button.pack(side="left", padx=10)


            if current_tab == "Settings":
                next_button.pack_forget()
                submit_button.pack(side="left", padx=10)
            else:
                submit_button.pack_forget()
                next_button.pack(side="left", padx=10)
            
            check_form_changed()
        
        tab_view.configure(command=on_tab_change) # Configure command after defining

        # --- DSG Prep Tab ---
        prep_tab = tab_view.tab("DSG Prep")
        prep_tab.grid_columnconfigure((0, 1), weight=1)
        prep_frame = ctk.CTkFrame(prep_tab)
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

        bible_frame = ctk.CTkFrame(prep_tab)
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

        # --- DSG Editions Tab ---
        editions_tab = tab_view.tab("DSG Editions")
        editions_tab.grid_columnconfigure((0, 1), weight=1)
        lang_options = [
            "English",
            "French",
            "German",
            "Italian",
            "Portuguese",
            "Russian",
            "Spanish",
        ]
        full_dsg_frame = ctk.CTkFrame(editions_tab)
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

        se_dsg_frame = ctk.CTkFrame(editions_tab)
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

        # --- Schedules Tab ---
        schedules_tab = tab_view.tab("Schedules")
        schedules_tab.grid_columnconfigure(0, weight=2)
        schedules_tab.grid_columnconfigure(1, weight=1)
        districts_frame = ctk.CTkFrame(schedules_tab)
        districts_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(districts_frame, text="Districts", font=("Arial", 14, "bold")).pack(
            pady=10
        )
        districts = [
            "British Columbia",
            "Alberta",
            "Saskatchewan",
            "Manitoba",
            "Northern Ontario",
            "Kitchener",
            "Hamilton",
            "Toronto",
            "Eastern Canada",
        ]
        district_vars = {
            d: ctk.IntVar(
                value=1
                if d in (saved_data["schedules_sub"].get("District Serving Schedules", []))
                else 0
            )
            for d in districts
        }
        for d in districts:
            ctk.CTkCheckBox(districts_frame, text=d, variable=district_vars[d]).pack(
                anchor="w", padx=10, pady=5
            )

        youth_seniors_frame = ctk.CTkFrame(schedules_tab)
        youth_seniors_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(
            youth_seniors_frame, text="Youth and Seniors", font=("Arial", 14, "bold")
        ).pack(pady=10)
        youth_var = ctk.IntVar(
            value=1 if "Youth Schedules" in saved_data["schedules_chosen"] else 0
        )
        seniors_var = ctk.IntVar(
            value=1 if "Seniors Schedules" in saved_data["schedules_chosen"] else 0
        )
        ctk.CTkCheckBox(youth_seniors_frame, text="Youth", variable=youth_var).pack(
            anchor="w", padx=10, pady=5
        )
        ctk.CTkCheckBox(youth_seniors_frame, text="Seniors", variable=seniors_var).pack(
            anchor="w", padx=10, pady=5
        )

        nacc_frame = ctk.CTkFrame(schedules_tab)
        nacc_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(nacc_frame, text="NACC", font=("Arial", 14, "bold")).pack(pady=10)
        nacc_var = ctk.IntVar(
            value=1 if "NACC Calendars" in saved_data["schedules_chosen"] else 0
        )
        ctk.CTkCheckBox(nacc_frame, text="NACC Calendar", variable=nacc_var).pack(
            anchor="w", padx=10, pady=5
        )
        
        # --- Ministers Tab ---
        ministers_tab = tab_view.tab("Ministers")
        current_ministers = _load_json_env("MINISTER_COLORS") or {}
        
        minister_frame_container = ctk.CTkFrame(ministers_tab)
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
                check_form_changed()
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
            check_form_changed()

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
                check_form_changed()
        
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

        # --- Settings Tab ---
        settings_tab = tab_view.tab("Settings")
        settings_tab.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(settings_tab, text="Login Credentials", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="w")
        
        ctk.CTkLabel(settings_tab, text="Username:").grid(row=1, column=0, padx=20, pady=5, sticky="w")
        username_entry = ctk.CTkEntry(settings_tab)
        username_entry.grid(row=1, column=1, padx=20, pady=5, sticky="ew")
        username_entry.insert(0, saved_data["USERNAME"])

        ctk.CTkLabel(settings_tab, text="Password:").grid(row=2, column=0, padx=20, pady=5, sticky="w")
        
        password_entry = ctk.CTkEntry(settings_tab, show="*")
        password_entry.grid(row=2, column=1, padx=20, pady=5, sticky="ew")
        password_entry.insert(0, saved_data["PASSWORD"])

        def toggle_password_visibility():
            if password_entry.cget("show") == "*":
                # Switch to visible
                password_entry.configure(show="")
                password_toggle_button.configure(text="Hide") 
            else:
                # Switch to hidden
                password_entry.configure(show="*")
                password_toggle_button.configure(text="Show")

        password_toggle_button = ctk.CTkButton(settings_tab, text="Show", width=80, command=toggle_password_visibility)
        password_toggle_button.grid(row=2, column=2, padx=10, pady=5)


        ctk.CTkLabel(settings_tab, text="File Save Location", font=("Arial", 16, "bold")).grid(row=3, column=0, columnspan=2, padx=20, pady=(20, 5), sticky="w")
        ctk.CTkLabel(settings_tab, text="This is where the downloaded files will be saved.").grid(row=4, column=0, columnspan=2, padx=20, pady=(0,10), sticky="w")

        ctk.CTkLabel(settings_tab, text="Save Path:").grid(row=5, column=0, padx=20, pady=5, sticky="w")
        
        path_entry = ctk.CTkEntry(settings_tab)
        path_entry.grid(row=5, column=1, sticky="ew", padx=20, pady=5)
        path_entry.insert(0, saved_data["DSGS_DIR"])

        def browse_path():
            directory = filedialog.askdirectory()
            if directory:
                path_entry.delete(0, "end")
                path_entry.insert(0, directory)

        browse_button = ctk.CTkButton(settings_tab, text="Browse...", command=browse_path, width=80)
        browse_button.grid(row=5, column=2, padx=10, pady=5)
        
        
        all_vars = (
            list(prep_vars.values())
            + list(bible_vars.values())
            + list(full_lang_vars.values())
            + list(se_lang_vars.values())
            + list(district_vars.values())
            + [youth_var, seniors_var, nacc_var]
        )

        result: Dict[str, Any] = {}

        def check_form_changed(*args):
            is_changed = any(v.get() for v in all_vars) or current_ministers
            submit_button.configure(state="normal" if is_changed else "disabled")

        for var in all_vars:
            var.trace_add("write", check_form_changed)

        def navigate_next():
            current_index = tab_names.index(tab_view.get())
            if current_index + 1 < len(tab_names):
                tab_view.set(tab_names[current_index + 1])
                on_tab_change()
        
        def navigate_back():
            current_index = tab_names.index(tab_view.get())
            if current_index - 1 >= 0:
                tab_view.set(tab_names[current_index -1])
                on_tab_change()

        def on_submit():
            selections = {o for o, v in prep_vars.items() if v.get()}
            schedules_chosen = set()
            if youth_var.get():
                schedules_chosen.add("Youth Schedules")
            if seniors_var.get():
                schedules_chosen.add("Seniors Schedules")
            if nacc_var.get():
                schedules_chosen.add("NACC Calendars")
            schedules_sub = {}
            dist_selection = {d for d, v in district_vars.items() if v.get()}
            if dist_selection:
                schedules_chosen.add("District Serving Schedules")
                schedules_sub["District Serving Schedules"] = dist_selection
            result.update(
                {
                    "selections": selections,
                    "bible_reading_langs": {
                        o for o, v in bible_vars.items() if v.get()
                    },
                    "full_dsg_langs": {l for l, v in full_lang_vars.items() if v.get()},
                    "se_dsg_langs": {l for l, v in se_lang_vars.items() if v.get()},
                    "schedules_chosen": schedules_chosen,
                    "schedules_sub": schedules_sub,
                    "minister_colors": current_ministers,
                    "highlight_opacity": 0.5,
                }
            )
            
            _save_json_env("USERNAME", username_entry.get())
            _save_json_env("PASSWORD", password_entry.get())
            _save_json_env("DSGS_DIR", path_entry.get())

            app.destroy()

        button_frame = ctk.CTkFrame(app)
        button_frame.pack(pady=10, side="bottom")

        back_button = ctk.CTkButton(button_frame, text="Back", command=navigate_back, width=120)
        next_button = ctk.CTkButton(button_frame, text="Next", command=navigate_next, width=120)
        next_button.pack(side="left", padx=10)

        submit_button = ctk.CTkButton(button_frame, text="Submit", command=on_submit, width=120)
        ctk.CTkButton(button_frame, text="Cancel", command=app.destroy, width=120).pack(side="left", padx=10)

        on_tab_change() # Initial call with first tab
        check_form_changed()

        app.mainloop()

        if result:
            _save_json_env("DSG_UI_SELECTIONS", result.get("selections", []))
            _save_json_env(
                "DSG_UI_BIBLE_READING_LANGS", result.get("bible_reading_langs", [])
            )
            _save_json_env("DSG_UI_FULL_DSG_LANGS", result.get("full_dsg_langs", []))
            _save_json_env("DSG_UI_SE_DSG_LANGS", result.get("se_dsg_langs", []))
            _save_json_env(
                "DSG_UI_SCHEDULES_CHOSEN", result.get("schedules_chosen", [])
            )
            _save_json_env("DSG_UI_SCHEDULES_SUB", result.get("schedules_sub", {}))
            _save_json_env("MINISTER_COLORS", result.get("minister_colors", {}))
            return result
        return {}

    except ImportError:
        return _terminal_fallback(saved_data)
    except Exception:
        import traceback
        print("An error occurred with the GUI. Falling back to terminal.")
        print(traceback.format_exc())
        return _terminal_fallback(saved_data)


def _terminal_fallback(saved_data: Dict[str, Any]) -> Dict[str, Any]:
    # ... (terminal fallback implementation remains the same)
    return {}

if __name__ == "__main__":
    get_user_selection()
