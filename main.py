
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime
import csv
import os
import db_manager

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# ==========================================================
# APPLICATION CONFIGURATION
# ==========================================================

BG = "#111111"
SIDEBAR = "#181818"
PANEL = "#202020"
PANEL_LIGHT = "#292929"
BUTTON_BG = "#353535"
BUTTON_HOVER = "#484848"
WHITE = "#F2F2F2"
MUTED = "#999999"
BORDER = "#383838"
ACCENT = "#BDBDBD"

FONT = "Segoe UI"

root = tk.Tk()
root.title("Health Monitoring System")
root.geometry("1250x780")
root.minsize(1050, 650)
root.configure(bg=BG)

current_page = "dashboard"
selected_record_id = None
form_entries = {}
history_tree = None
chart_canvas = None


# ==========================================================
# DATABASE HELPERS
# ==========================================================

def get_records():
    try:
        return db_manager.get_all_records()
    except Exception as error:
        messagebox.showerror("Database Error", str(error))
        return []


def get_latest_record():
    records = get_records()
    return records[0] if records else None


def format_value(value, suffix=""):
    if value is None or value == "":
        return "--"
    return f"{value}{suffix}"


# Expected record order:
# id, record_date, weight, heart_rate, systolic, diastolic,
# sleep_hours, water_litres, steps, notes


# ==========================================================
# GENERAL UI HELPERS
# ==========================================================

def clear_content():
    for widget in content.winfo_children():
        widget.destroy()


def make_label(parent, text, size=10, color=WHITE, bold=False):
    return tk.Label(
        parent,
        text=text,
        bg=parent.cget("bg"),
        fg=color,
        font=(FONT, size, "bold" if bold else "normal")
    )


def make_button(parent, text, command, primary=False, width=None):
    button = tk.Button(
        parent,
        text=text,
        command=command,
        bg=BUTTON_BG if not primary else "#555555",
        fg=WHITE,
        activebackground=BUTTON_HOVER,
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=(FONT, 10, "bold"),
        padx=18,
        pady=10,
        width=width
    )

    button.bind(
        "<Enter>",
        lambda event: button.config(bg=BUTTON_HOVER)
    )
    button.bind(
        "<Leave>",
        lambda event: button.config(
            bg="#555555" if primary else BUTTON_BG
        )
    )

    return button


def make_card(parent, title, value, subtitle="", column=None):
    card = tk.Frame(
        parent,
        bg=PANEL,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    make_label(
        card, title.upper(), 9, MUTED, True
    ).pack(anchor="w", padx=18, pady=(16, 7))

    make_label(
        card, value, 23, WHITE, True
    ).pack(anchor="w", padx=18)

    if subtitle:
        make_label(
            card, subtitle, 9, MUTED
        ).pack(anchor="w", padx=18, pady=(5, 15))
    else:
        tk.Frame(card, bg=PANEL, height=15).pack()

    return card


def page_heading(title, subtitle):
    heading = tk.Frame(content, bg=BG)
    heading.pack(fill="x", pady=(0, 22))

    make_label(
        heading, title, 24, WHITE, True
    ).pack(anchor="w")

    make_label(
        heading, subtitle, 10, MUTED
    ).pack(anchor="w", pady=(5, 0))

    return heading


def create_section(parent, title):
    section = tk.Frame(
        parent,
        bg=PANEL,
        highlightbackground=BORDER,
        highlightthickness=1
    )

    make_label(
        section, title, 12, WHITE, True
    ).pack(anchor="w", padx=18, pady=(15, 12))

    return section


# ==========================================================
# SIDEBAR NAVIGATION
# ==========================================================

sidebar = tk.Frame(root, bg=SIDEBAR, width=220)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

brand_area = tk.Frame(sidebar, bg=SIDEBAR)
brand_area.pack(fill="x", padx=22, pady=(30, 40))

make_label(
    brand_area, "HEALTH OS", 19, WHITE, True
).pack(anchor="w")

make_label(
    brand_area, "PERSONAL HEALTH SYSTEM", 8, MUTED, True
).pack(anchor="w", pady=(5, 0))

tk.Frame(sidebar, bg=BORDER, height=1).pack(
    fill="x", padx=18, pady=(0, 20)
)

navigation_buttons = {}


def show_page(page):
    global current_page

    current_page = page

    for key, button in navigation_buttons.items():
        button.config(
            bg="#3B3B3B" if key == page else SIDEBAR,
            fg=WHITE if key == page else MUTED
        )

    render_page()


def add_navigation_button(text, page, icon):
    button = tk.Button(
        sidebar,
        text=f"  {icon}   {text}",
        command=lambda: show_page(page),
        anchor="w",
        bg=SIDEBAR,
        fg=MUTED,
        activebackground=BUTTON_BG,
        activeforeground=WHITE,
        relief="flat",
        bd=0,
        cursor="hand2",
        font=(FONT, 10),
        padx=20,
        pady=14
    )

    button.pack(fill="x", padx=10, pady=3)
    navigation_buttons[page] = button


add_navigation_button("Dashboard", "dashboard", "▦")
add_navigation_button("Add Record", "add", "+")
add_navigation_button("History", "history", "☷")
add_navigation_button("Analytics", "analytics", "↗")
add_navigation_button("Settings", "settings", "⚙")

sidebar_bottom = tk.Frame(sidebar, bg=SIDEBAR)
sidebar_bottom.pack(side="bottom", fill="x", padx=20, pady=25)

tk.Frame(sidebar_bottom, bg=BORDER, height=1).pack(fill="x", pady=(0, 15))

make_label(
    sidebar_bottom, "HEALTH MONITORING SYSTEM", 8, MUTED
).pack(anchor="w")

make_label(
    sidebar_bottom, "Version 2.0", 8, MUTED
).pack(anchor="w", pady=(5, 0))


# ==========================================================
# MAIN CONTENT AREA
# ==========================================================

main_area = tk.Frame(root, bg=BG)
main_area.pack(side="right", fill="both", expand=True)

topbar = tk.Frame(main_area, bg=BG, height=65)
topbar.pack(fill="x", padx=30, pady=(15, 0))
topbar.pack_propagate(False)

topbar_title = tk.Label(
    topbar,
    text="PERSONAL HEALTH OVERVIEW",
    bg=BG,
    fg=MUTED,
    font=(FONT, 9, "bold")
)
topbar_title.pack(side="left", anchor="center")

date_label = tk.Label(
    topbar,
    text=date.today().strftime("%A, %d %B %Y"),
    bg=BG,
    fg=WHITE,
    font=(FONT, 9)
)
date_label.pack(side="right", anchor="center")

tk.Frame(main_area, bg=BORDER, height=1).pack(
    fill="x", padx=30, pady=(0, 20)
)

content = tk.Frame(main_area, bg=BG)
content.pack(fill="both", expand=True, padx=30, pady=(0, 25))


# ==========================================================
# DASHBOARD
# ==========================================================

def build_dashboard():
    records = get_records()

    page_heading(
        "Dashboard",
        "Your personal health overview and latest measurements."
    )

    latest = records[0] if records else None

    if latest:
        weight = format_value(latest[2], " kg")
        heart = format_value(latest[3], " bpm")

        if latest[4] and latest[5]:
            pressure = f"{latest[4]}/{latest[5]}"
        else:
            pressure = "--"

        sleep = format_value(latest[6], " hrs")
        water = format_value(latest[7], " L")
        steps = format_value(latest[8])
        latest_date = format_value(latest[1])
    else:
        weight = heart = pressure = sleep = water = steps = "--"
        latest_date = "No records yet"

    stats = tk.Frame(content, bg=BG)
    stats.pack(fill="x")

    stats.columnconfigure((0, 1, 2), weight=1, uniform="stats")

    cards = [
        ("BODY WEIGHT", weight, "Latest measurement"),
        ("HEART RATE", heart, "Beats per minute"),
        ("BLOOD PRESSURE", pressure, "Systolic / Diastolic"),
        ("SLEEP", sleep, "Hours recorded"),
        ("WATER INTAKE", water, "Litres recorded"),
        ("DAILY STEPS", steps, "Steps recorded")
    ]

    for index, (title, value, subtitle) in enumerate(cards):
        card = make_card(stats, title, value, subtitle)
        card.grid(
            row=index // 3,
            column=index % 3,
            sticky="nsew",
            padx=6,
            pady=6
        )

    info = tk.Frame(content, bg=BG)
    info.pack(fill="x", pady=(15, 12))

    make_label(
        info, f"Latest record: {latest_date}", 9, MUTED
    ).pack(side="left")

    make_button(
        info, "+ Add New Record",
        lambda: show_page("add"),
        primary=True
    ).pack(side="right")

    lower = tk.Frame(content, bg=BG)
    lower.pack(fill="both", expand=True)

    lower.columnconfigure(0, weight=3)
    lower.columnconfigure(1, weight=2)
    lower.rowconfigure(0, weight=1)

    # Weight chart
    chart_section = create_section(lower, "WEIGHT PROGRESS")
    chart_section.grid(
        row=0, column=0, sticky="nsew", padx=(0, 8)
    )

    if MATPLOTLIB_AVAILABLE and records:
        chart_frame = tk.Frame(chart_section, bg=PANEL)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=(0, 12))

        figure = Figure(figsize=(5, 3), dpi=100)
        figure.patch.set_facecolor(PANEL)

        axis = figure.add_subplot(111)
        axis.set_facecolor(PANEL)

        chronological = list(reversed(records))
        dates = [str(row[1]) for row in chronological]
        weights = [
            float(row[2]) for row in chronological
            if row[2] is not None
        ]

        if weights:
            dates = [
                str(row[1]) for row in chronological
                if row[2] is not None
            ]

            axis.plot(
                dates,
                weights,
                marker="o",
                linewidth=2,
                markersize=5
            )

        axis.set_ylabel("Weight (kg)", color=WHITE)
        axis.tick_params(colors=MUTED, labelsize=8)
        axis.grid(alpha=0.15)

        for spine in axis.spines.values():
            spine.set_color(BORDER)

        figure.autofmt_xdate()
        figure.tight_layout()

        canvas = FigureCanvasTkAgg(
            figure, master=chart_frame
        )
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    else:
        make_label(
            chart_section,
            "Add health records to view your weight progress.",
            10,
            MUTED
        ).pack(padx=20, pady=30)

    # Recent records
    recent_section = create_section(lower, "RECENT ACTIVITY")
    recent_section.grid(
        row=0, column=1, sticky="nsew", padx=(8, 0)
    )

    if records:
        for record in records[:5]:
            row = tk.Frame(recent_section, bg=PANEL)
            row.pack(fill="x", padx=15, pady=7)

            make_label(
                row, str(record[1]), 9, WHITE, True
            ).pack(side="left")

            value = (
                f"{record[2]} kg"
                if record[2] is not None else "--"
            )

            make_label(
                row, value, 9, MUTED
            ).pack(side="right")

            tk.Frame(
                recent_section, bg=BORDER, height=1
            ).pack(fill="x", padx=15)
    else:
        make_label(
            recent_section,
            "No health records available.",
            10,
            MUTED
        ).pack(padx=18, pady=25)


# ==========================================================
# ADD / EDIT RECORD
# ==========================================================

def build_add_record():
    global form_entries

    form_entries = {}

    title = "Edit Health Record" if selected_record_id else "Add Health Record"
    subtitle = (
        "Update the selected health record."
        if selected_record_id
        else "Enter your latest health measurements below."
    )

    page_heading(title, subtitle)

    form_card = tk.Frame(
        content,
        bg=PANEL,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    form_card.pack(fill="both", expand=True)

    make_label(
        form_card, "HEALTH INFORMATION", 12, WHITE, True
    ).pack(anchor="w", padx=25, pady=(22, 5))

    make_label(
        form_card,
        "Fields marked with an asterisk are required.",
        9,
        MUTED
    ).pack(anchor="w", padx=25, pady=(0, 20))

    fields_area = tk.Frame(form_card, bg=PANEL)
    fields_area.pack(fill="x", padx=25)

    fields_area.columnconfigure((0, 1), weight=1, uniform="fields")

    fields = [
        ("Record Date *", "record_date", date.today().isoformat()),
        ("Weight (kg)", "weight", ""),
        ("Heart Rate (bpm)", "heart_rate", ""),
        ("Systolic Pressure", "systolic", ""),
        ("Diastolic Pressure", "diastolic", ""),
        ("Sleep (hours)", "sleep_hours", ""),
        ("Water Intake (litres)", "water_litres", ""),
        ("Steps", "steps", "")
    ]

    for index, (label, key, default) in enumerate(fields):
        column = index % 2
        row = index // 2

        field_frame = tk.Frame(fields_area, bg=PANEL)
        field_frame.grid(
            row=row,
            column=column,
            sticky="ew",
            padx=(0, 20) if column == 0 else (20, 0),
            pady=9
        )

        make_label(
            field_frame, label, 9, MUTED, True
        ).pack(anchor="w", pady=(0, 7))

        entry = tk.Entry(
            field_frame,
            bg="#292929",
            fg=WHITE,
            insertbackground=WHITE,
            relief="flat",
            font=(FONT, 10),
            bd=0
        )
        entry.pack(fill="x", ipady=11)

        entry.insert(0, default)
        form_entries[key] = entry

    notes_frame = tk.Frame(form_card, bg=PANEL)
    notes_frame.pack(fill="x", padx=25, pady=(18, 5))

    make_label(
        notes_frame, "NOTES", 9, MUTED, True
    ).pack(anchor="w", pady=(0, 7))

    notes_text = tk.Text(
        notes_frame,
        height=4,
        bg="#292929",
        fg=WHITE,
        insertbackground=WHITE,
        relief="flat",
        font=(FONT, 10),
        wrap="word"
    )
    notes_text.pack(fill="x", ipady=5)

    form_entries["notes"] = notes_text

    # Load selected record when editing
    if selected_record_id:
        for record in get_records():
            if record[0] == selected_record_id:
                keys = [
                    "record_date", "weight", "heart_rate",
                    "systolic", "diastolic", "sleep_hours",
                    "water_litres", "steps"
                ]

                for index, key in enumerate(keys, start=1):
                    value = record[index]
                    if value is not None:
                        form_entries[key].delete(0, "end")
                        form_entries[key].insert(0, str(value))

                if record[9]:
                    notes_text.insert("1.0", str(record[9]))

                break

    buttons = tk.Frame(form_card, bg=PANEL)
    buttons.pack(fill="x", padx=25, pady=22)

    make_button(
        buttons,
        "Save Record" if not selected_record_id else "Update Record",
        save_record,
        primary=True
    ).pack(side="left")

    make_button(
        buttons, "Clear Form", clear_form
    ).pack(side="left", padx=10)


def clear_form():
    for key, widget in form_entries.items():
        if key == "record_date":
            widget.delete(0, "end")
            widget.insert(0, date.today().isoformat())
        elif key == "notes":
            widget.delete("1.0", "end")
        else:
            widget.delete(0, "end")


def get_form_data():
    values = {}

    for key, widget in form_entries.items():
        if key == "notes":
            values[key] = widget.get("1.0", "end").strip()
        else:
            values[key] = widget.get().strip()

    # Date validation
    try:
        datetime.strptime(values["record_date"], "%Y-%m-%d")
    except ValueError:
        messagebox.showerror(
            "Invalid Date",
            "Enter the date using YYYY-MM-DD format."
        )
        return None

    numeric_fields = {
        "weight": (1, 500, float),
        "heart_rate": (20, 250, int),
        "systolic": (40, 300, int),
        "diastolic": (20, 200, int),
        "sleep_hours": (0, 24, float),
        "water_litres": (0, 30, float),
        "steps": (0, 200000, int)
    }

    for key, (minimum, maximum, converter) in numeric_fields.items():
        value = values[key]

        if value == "":
            values[key] = None
            continue

        try:
            number = converter(value)
            if not minimum <= number <= maximum:
                raise ValueError
            values[key] = number
        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                f"Please enter a valid {key.replace('_', ' ')} "
                f"between {minimum} and {maximum}."
            )
            return None

    if (values["systolic"] is None) != (values["diastolic"] is None):
        messagebox.showerror(
            "Blood Pressure",
            "Enter both systolic and diastolic values."
        )
        return None

    if not any(values[key] is not None for key in numeric_fields):
        messagebox.showerror(
            "Missing Information",
            "Enter at least one health measurement."
        )
        return None

    return (
        values["record_date"],
        values["weight"],
        values["heart_rate"],
        values["systolic"],
        values["diastolic"],
        values["sleep_hours"],
        values["water_litres"],
        values["steps"],
        values["notes"]
    )


def save_record():
    global selected_record_id

    data = get_form_data()

    if data is None:
        return

    try:
        if selected_record_id:
            db_manager.update_record(selected_record_id, data)
            messagebox.showinfo(
                "Success", "Health record updated successfully."
            )
        else:
            db_manager.add_record(data)
            messagebox.showinfo(
                "Success", "Health record added successfully."
            )

        selected_record_id = None
        show_page("dashboard")

    except Exception as error:
        messagebox.showerror("Database Error", str(error))


# ==========================================================
# HISTORY
# ==========================================================

def build_history():
    global history_tree

    page_heading(
        "Health History",
        "Review, edit, delete and export your previous records."
    )

    toolbar = tk.Frame(content, bg=BG)
    toolbar.pack(fill="x", pady=(0, 15))

    make_button(
        toolbar, "+ Add Record",
        lambda: show_page("add"),
        primary=True
    ).pack(side="left")

    make_button(
        toolbar, "Edit Selected",
        edit_selected_record
    ).pack(side="left", padx=7)

    make_button(
        toolbar, "Delete Selected",
        delete_selected_record
    ).pack(side="left")

    make_button(
        toolbar, "Export CSV",
        export_csv
    ).pack(side="right")

    table_frame = tk.Frame(
        content,
        bg=PANEL,
        highlightbackground=BORDER,
        highlightthickness=1
    )
    table_frame.pack(fill="both", expand=True)

    columns = (
        "date", "weight", "heart", "pressure",
        "sleep", "water", "steps"
    )

    history_tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="headings",
        selectmode="browse"
    )

    headings = {
        "date": "DATE",
        "weight": "WEIGHT (KG)",
        "heart": "HEART RATE",
        "pressure": "BLOOD PRESSURE",
        "sleep": "SLEEP (HRS)",
        "water": "WATER (L)",
        "steps": "STEPS"
    }

    for column, heading in headings.items():
        history_tree.heading(column, text=heading)
        history_tree.column(column, width=120, anchor="center")

    history_tree.column("date", width=140)

    scrollbar = ttk.Scrollbar(
        table_frame,
        orient="vertical",
        command=history_tree.yview
    )
    history_tree.configure(yscrollcommand=scrollbar.set)

    history_tree.pack(
        side="left", fill="both", expand=True, padx=10, pady=10
    )
    scrollbar.pack(side="right", fill="y", pady=10)

    records = get_records()

    for record in records:
        pressure = (
            f"{record[4]}/{record[5]}"
            if record[4] is not None and record[5] is not None
            else "--"
        )

        history_tree.insert(
            "",
            "end",
            iid=str(record[0]),
            values=(
                record[1],
                format_value(record[2]),
                format_value(record[3]),
                pressure,
                format_value(record[6]),
                format_value(record[7]),
                format_value(record[8])
            )
        )

    if not records:
        make_label(
            content,
            "No records found. Add your first health record to get started.",
            10,
            MUTED
        ).pack(pady=15)


def edit_selected_record():
    global selected_record_id

    if history_tree is None:
        return

    selected = history_tree.selection()

    if not selected:
        messagebox.showwarning(
            "No Selection", "Select a record first."
        )
        return

    selected_record_id = int(selected[0])
    show_page("add")


def delete_selected_record():
    if history_tree is None:
        return

    selected = history_tree.selection()

    if not selected:
        messagebox.showwarning(
            "No Selection", "Select a record first."
        )
        return

    record_id = int(selected[0])

    confirm = messagebox.askyesno(
        "Confirm Delete",
        "Are you sure you want to delete this health record?"
    )

    if confirm:
        try:
            db_manager.delete_record(record_id)
            messagebox.showinfo(
                "Deleted", "Health record deleted successfully."
            )
            show_page("history")
        except Exception as error:
            messagebox.showerror("Database Error", str(error))


def export_csv():
    records = get_records()

    if not records:
        messagebox.showwarning(
            "No Data", "There are no records to export."
        )
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")],
        initialfile="health_records.csv"
    )

    if not file_path:
        return

    headers = [
        "ID", "Date", "Weight", "Heart Rate",
        "Systolic", "Diastolic", "Sleep Hours",
        "Water Litres", "Steps", "Notes"
    ]

    try:
        with open(
            file_path, "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(records)

        messagebox.showinfo(
            "Export Complete",
            f"Your records were exported to:\n{file_path}"
        )

    except Exception as error:
        messagebox.showerror("Export Error", str(error))


# ==========================================================
# ANALYTICS
# ==========================================================

def build_analytics():
    records = get_records()

    page_heading(
        "Health Analytics",
        "Visualise your measurements and monitor your progress."
    )

    chart_section = create_section(content, "WEIGHT TREND")
    chart_section.pack(fill="both", expand=True)

    if not records:
        make_label(
            chart_section,
            "No records available. Add health records to generate analytics.",
            10,
            MUTED
        ).pack(pady=35)
        return

    if not MATPLOTLIB_AVAILABLE:
        make_label(
            chart_section,
            "Matplotlib is not installed. Run: pip install matplotlib",
            10,
            MUTED
        ).pack(pady=35)
        return

    chronological = list(reversed(records))
    weight_records = [
        row for row in chronological if row[2] is not None
    ]

    if not weight_records:
        make_label(
            chart_section,
            "No weight measurements are available yet.",
            10,
            MUTED
        ).pack(pady=35)
        return

    figure = Figure(figsize=(8, 4), dpi=110)
    figure.patch.set_facecolor(PANEL)

    axis = figure.add_subplot(111)
    axis.set_facecolor(PANEL)

    dates = [str(row[1]) for row in weight_records]
    weights = [float(row[2]) for row in weight_records]

    axis.plot(
        dates,
        weights,
        marker="o",
        linewidth=2,
        markersize=6
    )

    axis.set_title(
        "Weight Progress",
        color=WHITE,
        fontsize=13,
        pad=15
    )
    axis.set_ylabel("Weight (kg)", color=WHITE)
    axis.set_xlabel("Date", color=WHITE)

    axis.tick_params(colors=MUTED, labelsize=8)
    axis.grid(alpha=0.15)

    for spine in axis.spines.values():
        spine.set_color(BORDER)

    figure.autofmt_xdate()
    figure.tight_layout()

    chart = FigureCanvasTkAgg(
        figure, master=chart_section
    )
    chart.draw()
    chart.get_tk_widget().pack(
        fill="both", expand=True, padx=15, pady=15
    )

    if len(weights) >= 2:
        difference = weights[-1] - weights[0]
        change_text = f"{difference:+.1f} kg"
    else:
        change_text = "Not enough data"

    summary = tk.Frame(content, bg=BG)
    summary.pack(fill="x", pady=15)

    summary.columnconfigure((0, 1, 2), weight=1)

    summary_cards = [
        ("TOTAL RECORDS", str(len(records))),
        ("WEIGHT ENTRIES", str(len(weight_records))),
        ("WEIGHT CHANGE", change_text)
    ]

    for index, (title, value) in enumerate(summary_cards):
        card = make_card(summary, title, value)
        card.grid(
            row=0, column=index, sticky="nsew", padx=6
        )


# ==========================================================
# SETTINGS
# ==========================================================

def build_settings():
    page_heading(
        "Settings",
        "Application information and configuration."
    )

    info_card = create_section(content, "APPLICATION INFORMATION")
    info_card.pack(fill="x", pady=(0, 15))

    information = [
        ("Application", "Health Monitoring System"),
        ("Version", "2.0"),
        ("Interface", "Tkinter Desktop Application"),
        ("Database", "SQLite"),
        ("Chart Library", "Matplotlib" if MATPLOTLIB_AVAILABLE else "Not installed")
    ]

    for label, value in information:
        row = tk.Frame(info_card, bg=PANEL)
        row.pack(fill="x", padx=20, pady=9)

        make_label(
            row, label, 10, MUTED
        ).pack(side="left")

        make_label(
            row, value, 10, WHITE, True
        ).pack(side="right")

    database_card = create_section(content, "DATABASE")
    database_card.pack(fill="x")

    database_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "database",
        "health_data.db"
    )

    make_label(
        database_card,
        "Your health records are stored locally using SQLite.",
        10,
        MUTED
    ).pack(anchor="w", padx=20, pady=(0, 8))

    path_label = tk.Label(
        database_card,
        text=database_path,
        bg=PANEL,
        fg=ACCENT,
        font=(FONT, 9),
        wraplength=750,
        justify="left"
    )
    path_label.pack(anchor="w", padx=20, pady=(0, 20))


# ==========================================================
# PAGE RENDERING
# ==========================================================

def render_page():
    clear_content()

    pages = {
        "dashboard": build_dashboard,
        "add": build_add_record,
        "history": build_history,
        "analytics": build_analytics,
        "settings": build_settings
    }

    page_function = pages.get(current_page, build_dashboard)
    page_function()


# ==========================================================
# APPLICATION STARTUP
# ==========================================================

try:
    db_manager.initialize_database()
except Exception as error:
    messagebox.showerror(
        "Database Error",
        f"Could not initialise the database:\n{error}"
    )

show_page("dashboard")

root.mainloop()

