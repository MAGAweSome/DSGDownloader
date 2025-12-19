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
    saved = {
        'selections': set(_load_json_env('DSG_UI_SELECTIONS') or []),
        'schedules_chosen': set(_load_json_env('DSG_UI_SCHEDULES_CHOSEN') or []),
        'schedules_sub': _load_json_env('DSG_UI_SCHEDULES_SUB') or {},
        'full_dsg_langs': set(_load_json_env('DSG_UI_FULL_DSG_LANGS') or []),
        'se_dsg_langs': set(_load_json_env('DSG_UI_SE_DSG_LANGS') or []),
        'bible_reading_langs': set(_load_json_env('DSG_UI_BIBLE_READING_LANGS') or []),
        'foreword_langs': set(_load_json_env('DSG_UI_FOREWORD_LANGS') or []),
        'bible_references_langs': set(_load_json_env('DSG_UI_BIBLE_REFERENCES_LANGS') or []),
    }

    # Try GUI
    try:
        import tkinter as tk
        from tkinter import ttk

        root = tk.Tk()
        root.title('DSG Downloader - Select Options')
        frm = ttk.Frame(root, padding=8)
        frm.grid(row=0, column=0, sticky='nsew')

        # schedules
        schedule_options = ['District Serving Schedules', 'NACC Calendars', 'Youth Schedules', 'Seniors Schedules']
        sched_vars = {s: tk.IntVar(value=1 if s in saved['schedules_chosen'] else 0) for s in schedule_options}
        ttk.Label(frm, text='Schedule groups:').grid(row=0, column=0, sticky='w')
        for i, s in enumerate(schedule_options, start=1):
            ttk.Checkbutton(frm, text=s, variable=sched_vars[s]).grid(row=i, column=0, sticky='w')

        # Districts
        districts = ['British Columbia', 'Alberta', 'Saskatchewan', 'Manitoba', 'Northern Ontario', 'Kitchener', 'Hamilton', 'Toronto', 'Eastern Canada']
        district_vars = {d: tk.IntVar(value=1 if d in (saved['schedules_sub'].get('District Serving Schedules') or []) else 0) for d in districts}
        ttk.Label(frm, text='Districts:').grid(row=0, column=1, sticky='w')
        for j, d in enumerate(districts, start=1):
            ttk.Checkbutton(frm, text=d, variable=district_vars[d]).grid(row=j, column=1, sticky='w')

        # Youth & Seniors
        youth_opts = ['Kitchener District', 'Hamilton District']
        youth_vars = {d: tk.IntVar(value=1 if d in (saved['schedules_sub'].get('Youth Schedules') or []) else 0) for d in youth_opts}
        ttk.Label(frm, text='Youth:').grid(row=0, column=2, sticky='w')
        for j, d in enumerate(youth_opts, start=1):
            ttk.Checkbutton(frm, text=d, variable=youth_vars[d]).grid(row=j, column=2, sticky='w')

        seniors_opts = ['Tri-District', 'Margaret Ave']
        seniors_vars = {d: tk.IntVar(value=1 if d in (saved['schedules_sub'].get('Seniors Schedules') or []) else 0) for d in seniors_opts}
        ttk.Label(frm, text='Seniors:').grid(row=0, column=3, sticky='w')
        for j, d in enumerate(seniors_opts, start=1):
            ttk.Checkbutton(frm, text=d, variable=seniors_vars[d]).grid(row=j, column=3, sticky='w')

        # extraction options
        options = ['English', 'French', 'Audio', 'Transcript', 'Bible Reading', 'Foreword', 'Full DSG', 'Bible References', 'Special Edition DSG']
        opt_vars = {o: tk.IntVar(value=1 if o in saved['selections'] else 0) for o in options}
        ttk.Label(frm, text='Extraction options:').grid(row=12, column=0, sticky='w')
        for k, o in enumerate(options, start=13):
            ttk.Checkbutton(frm, text=o, variable=opt_vars[o]).grid(row=k, column=0, sticky='w')

        lang_options = ['English', 'French', 'German', 'Italian', 'Portuguese', 'Russian', 'Spanish']
        full_lang_vars = {l: tk.IntVar(value=1 if l in saved['full_dsg_langs'] else 0) for l in lang_options}
        se_lang_vars = {l: tk.IntVar(value=1 if l in saved['se_dsg_langs'] else 0) for l in lang_options}
        foreword_lang_vars = {l: tk.IntVar(value=1 if l in saved['foreword_langs'] else 0) for l in ['English', 'French']}
        bibread_lang_vars = {l: tk.IntVar(value=1 if l in saved['bible_reading_langs'] else 0) for l in ['English', 'French']}
        bibref_lang_vars = {l: tk.IntVar(value=1 if l in saved['bible_references_langs'] else 0) for l in ['English', 'French']}

        ttk.Label(frm, text='Full DSG languages:').grid(row=12, column=1, sticky='w')
        for i, l in enumerate(lang_options, start=13):
            ttk.Checkbutton(frm, text=l, variable=full_lang_vars[l]).grid(row=i, column=1, sticky='w')

        ttk.Label(frm, text='Special Edition DSG languages:').grid(row=12, column=2, sticky='w')
        for i, l in enumerate(lang_options, start=13):
            ttk.Checkbutton(frm, text=l, variable=se_lang_vars[l]).grid(row=i, column=2, sticky='w')

        ttk.Label(frm, text='Foreword languages:').grid(row=20, column=1, sticky='w')
        for i, l in enumerate(['English', 'French'], start=21):
            ttk.Checkbutton(frm, text=l, variable=foreword_lang_vars[l]).grid(row=i, column=1, sticky='w')

        ttk.Label(frm, text='Bible Reading languages:').grid(row=20, column=2, sticky='w')
        for i, l in enumerate(['English', 'French'], start=21):
            ttk.Checkbutton(frm, text=l, variable=bibread_lang_vars[l]).grid(row=i, column=2, sticky='w')

        ttk.Label(frm, text='Bible References languages:').grid(row=20, column=3, sticky='w')
        for i, l in enumerate(['English', 'French'], start=21):
            ttk.Checkbutton(frm, text=l, variable=bibref_lang_vars[l]).grid(row=i, column=3, sticky='w')

        result: Dict[str, Any] = {}

        def on_submit():
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
            result.update({
                'schedules_chosen': chosen_sched,
                'schedules_sub': schedules_sub,
                'selections': selections_set,
                'full_dsg_langs': {l for l, v in full_lang_vars.items() if v.get()},
                'se_dsg_langs': {l for l, v in se_lang_vars.items() if v.get()},
                'foreword_langs': {l for l, v in foreword_lang_vars.items() if v.get()},
                'bible_reading_langs': {l for l, v in bibread_lang_vars.items() if v.get()},
                'bible_references_langs': {l for l, v in bibref_lang_vars.items() if v.get()},
            })
            root.destroy()

        # Check if this is the first time the app is running by seeing if any saved data exists
        is_first_run = not any([
            saved.get('selections'),
            saved.get('schedules_chosen'),
            saved.get('schedules_sub')
        ])

        remaining_seconds = tk.IntVar(value=5)

        # Only start the countdown if it is NOT the first run
        if not is_first_run:
            countdown_var = tk.StringVar(value=f"Auto-submit in {remaining_seconds.get()}s")
            ttk.Label(frm, textvariable=countdown_var).grid(row=39, column=0, columnspan=4, pady=(6, 0))

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
            ttk.Label(frm, text="First run detected: Please configure your options and click Submit.").grid(row=39, column=0, columnspan=4, pady=(6, 0))

        # attach traces to all IntVars to reset the countdown if a user interacts
        all_vars = list(sched_vars.values()) + list(district_vars.values()) + \
                   list(youth_vars.values()) + list(seniors_vars.values()) + \
                   list(opt_vars.values()) + list(full_lang_vars.values()) + \
                   list(se_lang_vars.values()) + list(foreword_lang_vars.values()) + \
                   list(bibread_lang_vars.values()) + list(bibref_lang_vars.values())
        
        for v in all_vars:
            try:
                # If it's the first run, we don't need reset_countdown because the timer isn't running
                if not is_first_run:
                    v.trace_add('write', lambda *a, v=v: reset_countdown())
            except Exception:
                pass

        def on_cancel():
            root.destroy()

        btns = ttk.Frame(frm)
        btns.grid(row=40, column=0, columnspan=4, pady=8)
        ttk.Button(btns, text='Submit', command=on_submit).grid(row=0, column=0, padx=6)
        ttk.Button(btns, text='Cancel', command=on_cancel).grid(row=0, column=1, padx=6)

        root.mainloop()

        if result:
            # save selections back to .env
            _save_json_env('DSG_UI_SELECTIONS', result.get('selections', []))
            _save_json_env('DSG_UI_SCHEDULES_CHOSEN', result.get('schedules_chosen', []))
            _save_json_env('DSG_UI_SCHEDULES_SUB', result.get('schedules_sub', {}))
            _save_json_env('DSG_UI_FULL_DSG_LANGS', result.get('full_dsg_langs', []))
            _save_json_env('DSG_UI_SE_DSG_LANGS', result.get('se_dsg_langs', []))
            _save_json_env('DSG_UI_BIBLE_READING_LANGS', result.get('bible_reading_langs', []))
            _save_json_env('DSG_UI_FOREWORD_LANGS', result.get('foreword_langs', []))
            _save_json_env('DSG_UI_BIBLE_REFERENCES_LANGS', result.get('bible_references_langs', []))
            return result
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

    sel_display: Dict[str, Any] = {
        'selections': selections,
        'bible_reading_langs': bible_reading_langs,
        'full_dsg_langs': full_dsg_langs,
        'se_dsg_langs': se_dsg_langs,
        'foreword_langs': foreword_langs,
        'bible_references_langs': bible_references_langs,
        'schedules_chosen': schedules_chosen,
        'schedules_sub': schedules_sub,
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