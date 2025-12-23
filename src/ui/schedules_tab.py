"""UI components for the Schedules tab"""

import customtkinter as ctk

def create_schedules_tab(tab, saved_data):
    """Creates the Schedules tab and its widgets."""
    tab.grid_columnconfigure(0, weight=2)
    tab.grid_columnconfigure(1, weight=1)
    districts_frame = ctk.CTkFrame(tab)
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

    youth_seniors_frame = ctk.CTkFrame(tab)
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

    nacc_frame = ctk.CTkFrame(tab)
    nacc_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
    ctk.CTkLabel(nacc_frame, text="NACC", font=("Arial", 14, "bold")).pack(pady=10)
    nacc_var = ctk.IntVar(
        value=1 if "NACC Calendars" in saved_data["schedules_chosen"] else 0
    )
    ctk.CTkCheckBox(nacc_frame, text="NACC Calendar", variable=nacc_var).pack(
        anchor="w", padx=10, pady=5
    )
    
    return district_vars, youth_var, seniors_var, nacc_var
