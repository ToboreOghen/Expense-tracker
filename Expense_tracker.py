import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sqlite3
from datetime import date, datetime

# ---------------- Database Setup ----------------
conn = sqlite3.connect("expenses.db")
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        expense_date TEXT NOT NULL
    )
""")
conn.commit()

# Globals for mapping UI rows -> DB ids and tracking current filter
displayed_ids = []
current_filter = date.today().isoformat()

# ---------------- Functions ----------------
def add_expense():
    desc = desc_entry.get().strip()
    try:
        amt = float(amount_entry.get())
    except ValueError:
        messagebox.showwarning("Input Error", "Amount must be a number!")
        return

    if desc == "":
        messagebox.showwarning("Input Error", "Please enter a description!")
        return

    chosen_date = calendar_entry.get().strip()
    try:
        # validate YYYY-MM-DD
        datetime.strptime(chosen_date, "%Y-%m-%d")
    except ValueError:
        messagebox.showwarning("Date Error", "Enter date as YYYY-MM-DD")
        return

    c.execute("INSERT INTO expenses (description, amount, expense_date) VALUES (?, ?, ?)",
              (desc, amt, chosen_date))
    conn.commit()
    desc_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)
    load_expenses(chosen_date)


def delete_expense():
    sel = expense_list.curselection()
    if not sel:
        messagebox.showwarning("Selection Error", "Please select an expense to delete!")
        return

    idx = sel[0]
    try:
        row_id = displayed_ids[idx]
    except (IndexError, NameError):
        messagebox.showwarning("Selection Error", "Unable to determine selected record.")
        return

    # Confirm delete
    if not messagebox.askyesno("Confirm Delete", "Delete selected expense?"):
        return

    c.execute("DELETE FROM expenses WHERE id = ?", (row_id,))
    conn.commit()
    # reload same filter
    load_expenses(current_filter)


def load_expenses(filter_date=None):
    global displayed_ids, current_filter
    displayed_ids = []

    # Determine filter_date if none provided
    if filter_date is None:
        sel = selected_date.get()
        if sel == "Today":
            filter_date = date.today().isoformat()
        elif sel == "All":
            filter_date = "All"
        else:
            filter_date = sel

    # Normalize special tokens
    if filter_date == "Today":
        filter_date = date.today().isoformat()

    current_filter = filter_date

    expense_list.delete(0, tk.END)

    if filter_date == "All":
        c.execute("SELECT id, description, amount, expense_date FROM expenses ORDER BY expense_date ASC, id ASC")
        rows = c.fetchall()
    else:
        # assume filter_date is a YYYY-MM-DD string
        c.execute("SELECT id, description, amount, expense_date FROM expenses WHERE expense_date = ? ORDER BY id ASC", (filter_date,))
        rows = c.fetchall()

    total = 0.0
    for idx, (row_id, desc, amt, exp_date) in enumerate(rows, start=1):
        displayed_ids.append(row_id)
        expense_list.insert(tk.END, f"{idx} | {desc} | ${amt:.2f} | {exp_date}")
        total += amt

    total_label.config(text=f"Total Spent: ${total:.2f}")


def show_by_date():
    chosen = calendar_entry.get().strip()
    try:
        datetime.strptime(chosen, "%Y-%m-%d")  # validate date format
        load_expenses(chosen)
    except ValueError:
        messagebox.showwarning("Date Error", "Enter date as YYYY-MM-DD")


def exit_app():
    conn.close()
    root.destroy()


# ---------------- GUI Setup ----------------
root = tk.Tk()
root.title("Expense Tracker")
root.geometry("700x500")
root.config(bg="lightblue")

# Title
title_label = tk.Label(root, text="Expense Tracker", font=("Arial", 18, "bold"), bg="lightblue")
title_label.pack(pady=10)

# Entry Frame
entry_frame = tk.Frame(root, bg="lightblue")
entry_frame.pack(pady=5)

desc_label = tk.Label(entry_frame, text="Description:", font=("Arial", 12), bg="lightblue")
desc_label.grid(row=0, column=0, padx=5, pady=5)
desc_entry = tk.Entry(entry_frame, font=("Arial", 12), width=30)
desc_entry.grid(row=0, column=1, padx=5, pady=5)

amount_label = tk.Label(entry_frame, text="Amount:", font=("Arial", 12), bg="lightblue")
amount_label.grid(row=1, column=0, padx=5, pady=5)
amount_entry = tk.Entry(entry_frame, font=("Arial", 12), width=20)
amount_entry.grid(row=1, column=1, padx=5, pady=5)

# Buttons
button_frame = tk.Frame(root, bg="lightblue")
button_frame.pack(pady=10)

add_button = tk.Button(button_frame, text="Add Expense", font=("Arial", 12), width=12, command=add_expense)
add_button.grid(row=0, column=0, padx=5)

delete_button = tk.Button(button_frame, text="Delete Expense", font=("Arial", 12), width=12, command=delete_expense)
delete_button.grid(row=0, column=1, padx=5)

exit_button = tk.Button(button_frame, text="Exit", font=("Arial", 12), width=12, command=exit_app)
exit_button.grid(row=1, column=0, padx=5)

# Date Filter Frame
filter_frame = tk.Frame(root, bg="lightblue")
filter_frame.pack(pady=10)

selected_date = tk.StringVar(value="Today")

date_options = ["Today", "All"]
date_menu = ttk.Combobox(filter_frame, textvariable=selected_date, values=date_options, state="readonly", width=10)
date_menu.grid(row=0, column=0, padx=5)
date_menu.bind("<<ComboboxSelected>>", lambda e: load_expenses(selected_date.get()))

calendar_entry = tk.Entry(filter_frame, font=("Arial", 12), width=12)
calendar_entry.grid(row=0, column=1, padx=5)
calendar_entry.insert(0, date.today().isoformat())

calendar_button = tk.Button(filter_frame, text="View Date", font=("Arial", 10), command=show_by_date)
calendar_button.grid(row=0, column=2, padx=5)

# Expense List with Scrollbars
list_frame = tk.Frame(root)
list_frame.pack(pady=10, fill=tk.BOTH, expand=True)

xscrollbar = tk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)

yscrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL)
yscrollbar.pack(side=tk.RIGHT, fill=tk.Y)

expense_list = tk.Listbox(
    list_frame, font=("Courier", 12), width=70, height=12,
    yscrollcommand=yscrollbar.set, xscrollcommand=xscrollbar.set
)
expense_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

yscrollbar.config(command=expense_list.yview)
xscrollbar.config(command=expense_list.xview)

# Total Label
total_label = tk.Label(root, text="Total Spent: $0.00", font=("Arial", 14, "bold"), bg="lightblue")
total_label.pack(pady=10)

# Load today's data at start
load_expenses("Today")

# Run App
root.mainloop()
