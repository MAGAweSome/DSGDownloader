def prompt_multichoice(prompt, choices):
    """Prompt user to pick one or more choices.

    - `choices` is a list of display strings.
    Returns a set of normalized choice keys (lowercase display text).
    """
    print(prompt)
    for i, c in enumerate(choices, start=1):
        print(f"{i}) {c}")
    raw = input("Enter choices (comma-separated, numbers or names): ").strip()
    if not raw:
        return set()
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    selected = set()
    for p in parts:
        # try number
        if p.isdigit():
            idx = int(p) - 1
            if 0 <= idx < len(choices):
                selected.add(choices[idx].lower())
            continue
        # match by name (case-insensitive)
        low = p.lower()
        for c in choices:
            if low == c.lower() or low == c.lower().replace(' ', ''):
                selected.add(c.lower())
                break
    return selected


def prompt_languages(prompt, langs):
    print(prompt)
    for i, c in enumerate(langs, start=1):
        print(f"{i}) {c}")
    raw = input("Enter languages (comma-separated, numbers or names; leave empty for none): ").strip()
    if not raw:
        return set()
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    selected = set()
    for p in parts:
        if p.isdigit():
            idx = int(p) - 1
            if 0 <= idx < len(langs):
                selected.add(langs[idx])
            continue
        for c in langs:
            if p.lower() == c.lower():
                selected.add(c)
                break
    return selected


def get_user_selection():
    """Interactive UI: ask the user which items to extract and language details.

    Returns a dict with keys:
      - selections: set of selected option keys (lowercase names)
      - bible_reading_langs: set of languages for Bible Reading (if selected)
      - full_dsg_langs: set of languages for Full DSG (if selected)
      - se_dsg_langs: set of languages for Special Edition DSG (if selected)
    """
    # First ask about Schedules selections (districts, NACC, youth, seniors)
    schedule_options = [
        "District Serving Schedules",
        "NACC Calendars",
        "Youth Schedules",
        "Seniors Schedules",
    ]

    schedules_chosen = prompt_multichoice("Which schedule groups would you like to include?", schedule_options)

    # For each chosen schedule group, ask follow-ups
    schedules_sub = {}
    if 'district serving schedules' in schedules_chosen:
        districts = [
            'British Columbia', 'Alberta', 'Saskatchewan', 'Manitoba', 'Northern Ontario',
            'Kitchener', 'Hamilton', 'Toronto', 'Eastern Canada'
        ]
        sel = prompt_multichoice("Which district serving schedules? (multiple OK)", districts)
        schedules_sub['District Serving Schedules'] = sel

    if 'nacc calendars' in schedules_chosen:
        nacc_opts = ['National', 'Districts']
        sel = prompt_multichoice("Which NACC Calendars?", nacc_opts)
        schedules_sub['NACC Calendars'] = sel

    if 'youth schedules' in schedules_chosen:
        youth_opts = ['Kitchener District', 'Hamilton District']
        sel = prompt_multichoice("Which Youth schedules?", youth_opts)
        schedules_sub['Youth Schedules'] = sel

    if 'seniors schedules' in schedules_chosen:
        seniors_opts = ['Tri-District', 'Margaret Ave']
        sel = prompt_multichoice("Which Seniors schedules?", seniors_opts)
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

    selections = prompt_multichoice("Which items would you like to extract?", options)

    # follow-ups
    bible_reading_langs = set()
    if "bible reading" in selections:
        bible_reading_langs = prompt_languages(
            "Bible Reading languages (choose one or both):", ["English", "French"]
        )
        if not bible_reading_langs:
            # default to both if user enters nothing
            bible_reading_langs = {"English", "French"}

    lang_options = ["English", "French", "German", "Italian", "Portuguese", "Russian", "Spanish"]
    full_dsg_langs = set()
    se_dsg_langs = set()
    foreword_langs = set()
    bible_references_langs = set()
    if "full dsg" in selections:
        full_dsg_langs = prompt_languages("Full DSG languages (choose any):", lang_options)
    if "special edition dsg" in selections:
        se_dsg_langs = prompt_languages("Special Edition DSG languages (choose any):", lang_options)
    if "foreword" in selections:
        foreword_langs = prompt_languages("Foreword languages (choose one or both):", ["English", "French"]) or {"English", "French"}
    if "bible references" in selections:
        bible_references_langs = prompt_languages("Bible References languages (choose one or both):", ["English", "French"]) or {"English", "French"}

    sel_display = {
        'selections': selections,
        'bible_reading_langs': bible_reading_langs,
        'full_dsg_langs': full_dsg_langs,
        'se_dsg_langs': se_dsg_langs,
        'foreword_langs': foreword_langs,
        'bible_references_langs': bible_references_langs,
    }

    # include schedules choices
    sel_display['schedules_chosen'] = schedules_chosen
    sel_display['schedules_sub'] = schedules_sub

    # print summary
    print("\nUser has selected:")
    if selections:
        for s in sorted(selections):
            print(f"- {s}")
    else:
        print("- (none)")
    if "bible reading" in selections:
        print("Bible Reading languages:", ", ".join(sorted(bible_reading_langs)))
    if "full dsg" in selections:
        print("Full DSG languages:", ", ".join(sorted(full_dsg_langs)) if full_dsg_langs else "(none)")
    if "special edition dsg" in selections:
        print("Special Edition DSG languages:", ", ".join(sorted(se_dsg_langs)) if se_dsg_langs else "(none)")
    if "foreword" in selections:
        print("Foreword languages:", ", ".join(sorted(foreword_langs)) if foreword_langs else "(none)")
    if "bible references" in selections:
        print("Bible References languages:", ", ".join(sorted(bible_references_langs)) if bible_references_langs else "(none)")

    if schedules_chosen:
        print("Schedule groups selected:")
        for s in sorted(schedules_chosen):
            print(f"- {s}")
            subs = schedules_sub.get(s.title(), schedules_sub.get(s, set()))
            if subs:
                print("  choices:", ", ".join(sorted(subs)))

    return sel_display
