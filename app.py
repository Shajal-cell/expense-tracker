from flask import Flask, render_template, request, redirect, url_for
import json
from datetime import datetime

app = Flask(__name__)

# --- Load and Save Functions ---
def load_expenses():
    try:
        with open("expenses.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

def save_expenses(expenses):
    with open("expenses.json", "w") as file:
        json.dump(expenses, file, indent=4)

def load_budgets():
    try:
        with open("budgets.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_budgets(budgets):
    with open("budgets.json", "w") as file:
        json.dump(budgets, file, indent=4)

# --- NEW: Landing Page Route ---
@app.route("/")
def landing():
    return render_template("landing.html")

# --- UPDATED: Tracker Page Route ---
@app.route("/tracker", methods=["GET", "POST"])
def tracker():
    expenses = load_expenses()
    budgets = load_budgets()

    if request.method == "POST":
        new_expense = {
            "amount": float(request.form.get("amount")),
            "category": request.form.get("category"),
            "description": request.form.get("description"),
            "date": request.form.get("date")
        }
        expenses.append(new_expense)
        save_expenses(expenses)
        return redirect(url_for("tracker"))

    total_spending = 0
    raw_monthly_totals = {}

    for expense in expenses:
        amount = expense["amount"]
        total_spending += amount

        date_str = expense.get("date", "")
        if len(date_str) >= 7:
            year_month = date_str[:7]
            if year_month in raw_monthly_totals:
                raw_monthly_totals[year_month] += amount
            else:
                raw_monthly_totals[year_month] = amount

    monthly_data = []
    for key in sorted(raw_monthly_totals.keys()):
        dt = datetime.strptime(key, "%Y-%m")
        formatted = dt.strftime("%B %Y")
        total = raw_monthly_totals[key]
        budget = budgets.get(key, 2000.0) 
        
        monthly_data.append({
            "formatted_name": formatted,
            "total": total,
            "budget": budget
        })

    return render_template("index.html", expenses=expenses, total=total_spending, monthly_data=monthly_data)

@app.route("/set_budget", methods=["POST"])
def set_budget():
    budgets = load_budgets()
    month_key = request.form.get("month")
    amount = float(request.form.get("amount"))
    
    budgets[month_key] = amount
    save_budgets(budgets)
    return redirect(url_for("tracker"))

@app.route("/delete/<int:expense_id>")
def delete_expense(expense_id):
    expenses = load_expenses()
    if 0 <= expense_id < len(expenses):
        expenses.pop(expense_id)
        save_expenses(expenses)
    return redirect(url_for("tracker"))

@app.route("/charts")
def charts():
    expenses = load_expenses()
    available_months = {}
    for exp in expenses:
        date_str = exp.get("date", "")
        if len(date_str) >= 7:
            ym = date_str[:7]
            if ym not in available_months:
                dt = datetime.strptime(ym, "%Y-%m")
                available_months[ym] = dt.strftime("%B %Y")
                
    selected_month = request.args.get("month", "all")
    
    category_totals = {}
    for exp in expenses:
        date_str = exp.get("date", "")
        if selected_month != "all" and date_str[:7] != selected_month:
            continue
        cat = exp["category"]
        category_totals[cat] = category_totals.get(cat, 0) + exp["amount"]
        
    categories = list(category_totals.keys())
    amounts = list(category_totals.values())
    
    return render_template("charts.html", categories=categories, amounts=amounts, available_months=available_months, selected_month=selected_month)

if __name__ == "__main__":
    app.run(debug=True)