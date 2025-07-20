
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

app = Flask(__name__)
app.secret_key = 'expense_tracker_secret_key_2024'

# Data storage file
DATA_FILE = 'expenses_data.json'

# Currency configurations
CURRENCIES = {
    'USD': {'symbol': '$', 'name': 'US Dollar'},
    'EUR': {'symbol': '€', 'name': 'Euro'},
    'GBP': {'symbol': '£', 'name': 'British Pound'},
    'JPY': {'symbol': '¥', 'name': 'Japanese Yen'},
    'INR': {'symbol': '₹', 'name': 'Indian Rupee'},
    'CAD': {'symbol': 'C$', 'name': 'Canadian Dollar'},
    'AUD': {'symbol': 'A$', 'name': 'Australian Dollar'},
    'CNY': {'symbol': '¥', 'name': 'Chinese Yuan'}
}

def load_data():
    """Load expense data from JSON file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                # Ensure all required fields exist
                if 'settings' not in data:
                    data['settings'] = {'currency': 'USD', 'theme': 'light'}
                if 'goals' not in data:
                    data['goals'] = []
                if 'recurring_expenses' not in data:
                    data['recurring_expenses'] = []
                return data
        except:
            return {
                'expenses': [], 
                'budgets': {}, 
                'categories': [],
                'settings': {'currency': 'USD', 'theme': 'light'},
                'goals': [],
                'recurring_expenses': []
            }
    return {
        'expenses': [], 
        'budgets': {}, 
        'categories': [],
        'settings': {'currency': 'USD', 'theme': 'light'},
        'goals': [],
        'recurring_expenses': []
    }

def save_data(data):
    """Save expense data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Default categories for new users
DEFAULT_CATEGORIES = [
    'Food & Dining', 'Transportation', 'Shopping', 'Entertainment',
    'Bills & Utilities', 'Healthcare', 'Education', 'Travel',
    'Groceries', 'Gas', 'Other'
]

@app.route('/')
def dashboard():
    """Main dashboard showing overview of expenses and budgets"""
    data = load_data()
    
    # Initialize categories if empty
    if not data['categories']:
        data['categories'] = DEFAULT_CATEGORIES
        save_data(data)
    
    # Get current month data
    now = datetime.now()
    current_month = now.strftime('%Y-%m')
    
    # Filter expenses for current month
    current_month_expenses = [
        exp for exp in data['expenses'] 
        if exp['date'].startswith(current_month)
    ]
    
    # Calculate totals by category
    category_totals = defaultdict(float)
    total_spent = 0
    
    for expense in current_month_expenses:
        category_totals[expense['category']] += expense['amount']
        total_spent += expense['amount']
    
    # Get budget vs actual
    budgets = data.get('budgets', {})
    total_budget = sum(budgets.values())
    budget_remaining = total_budget - total_spent
    
    # Recent transactions (last 5)
    recent_expenses = sorted(data['expenses'], key=lambda x: x['date'], reverse=True)[:5]
    
    return render_template('dashboard.html', 
                         category_totals=dict(category_totals),
                         total_spent=total_spent,
                         total_budget=total_budget,
                         budget_remaining=budget_remaining,
                         recent_expenses=recent_expenses,
                         current_month=now.strftime('%B %Y'))

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    """Add new expense"""
    data = load_data()
    
    if request.method == 'POST':
        try:
            expense = {
                'id': len(data['expenses']) + 1,
                'amount': float(request.form['amount']),
                'category': request.form['category'],
                'description': request.form['description'],
                'date': request.form['date'],
                'currency': data['settings']['currency'],
                'created_at': datetime.now().isoformat()
            }
            
            data['expenses'].append(expense)
            save_data(data)
            flash('Expense added successfully!', 'success')
            return redirect(url_for('dashboard'))
        except ValueError:
            flash('Please enter a valid amount!', 'error')
    
    currency = data['settings']['currency']
    return render_template('add_expense.html', 
                         categories=data['categories'],
                         currency=currency,
                         currency_symbol=CURRENCIES[currency]['symbol'])

@app.route('/expenses')
def view_expenses():
    """View all expenses with filtering options"""
    data = load_data()
    
    # Get filter parameters
    month_filter = request.args.get('month', '')
    category_filter = request.args.get('category', '')
    
    expenses = data['expenses']
    
    # Apply filters
    if month_filter:
        expenses = [exp for exp in expenses if exp['date'].startswith(month_filter)]
    
    if category_filter:
        expenses = [exp for exp in expenses if exp['category'] == category_filter]
    
    # Sort by date (newest first)
    expenses = sorted(expenses, key=lambda x: x['date'], reverse=True)
    
    return render_template('expenses.html', 
                         expenses=expenses,
                         categories=data['categories'],
                         selected_month=month_filter,
                         selected_category=category_filter)

@app.route('/budgets', methods=['GET', 'POST'])
def manage_budgets():
    """Manage monthly budgets"""
    data = load_data()
    
    if request.method == 'POST':
        category = request.form['category']
        try:
            amount = float(request.form['amount'])
            data['budgets'][category] = amount
            save_data(data)
            flash(f'Budget for {category} set to ${amount:.2f}', 'success')
        except ValueError:
            flash('Please enter a valid budget amount!', 'error')
    
    return render_template('budgets.html', 
                         budgets=data.get('budgets', {}),
                         categories=data['categories'])

@app.route('/analytics')
def analytics():
    """Analytics and insights page"""
    data = load_data()
    
    # Monthly spending analysis
    monthly_totals = defaultdict(float)
    category_analysis = defaultdict(list)
    
    for expense in data['expenses']:
        month = expense['date'][:7]  # YYYY-MM format
        monthly_totals[month] += expense['amount']
        category_analysis[expense['category']].append(expense['amount'])
    
    # Category averages and totals
    category_stats = {}
    for category, amounts in category_analysis.items():
        category_stats[category] = {
            'total': sum(amounts),
            'average': sum(amounts) / len(amounts) if amounts else 0,
            'count': len(amounts)
        }
    
    # Get last 6 months for trending
    months_data = []
    for i in range(6):
        date = datetime.now() - timedelta(days=30*i)
        month_key = date.strftime('%Y-%m')
        month_name = date.strftime('%B %Y')
        months_data.append({
            'month': month_name,
            'amount': monthly_totals.get(month_key, 0)
        })
    
    months_data.reverse()
    
    return render_template('analytics.html',
                         monthly_data=months_data,
                         category_stats=category_stats)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """App settings and category management"""
    data = load_data()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_category':
            new_category = request.form['new_category'].strip()
            if new_category and new_category not in data['categories']:
                data['categories'].append(new_category)
                save_data(data)
                flash(f'Category "{new_category}" added successfully!', 'success')
            else:
                flash('Category already exists or is empty!', 'error')
        
        elif action == 'remove_category':
            category_to_remove = request.form['category_to_remove']
            if category_to_remove in data['categories']:
                data['categories'].remove(category_to_remove)
                # Remove from budgets too
                if category_to_remove in data.get('budgets', {}):
                    del data['budgets'][category_to_remove]
                save_data(data)
                flash(f'Category "{category_to_remove}" removed successfully!', 'success')
        
        elif action == 'update_currency':
            new_currency = request.form['currency']
            if new_currency in CURRENCIES:
                data['settings']['currency'] = new_currency
                save_data(data)
                flash(f'Currency updated to {CURRENCIES[new_currency]["name"]}!', 'success')
        
        elif action == 'update_theme':
            new_theme = request.form['theme']
            data['settings']['theme'] = new_theme
            save_data(data)
            flash('Theme updated successfully!', 'success')
    
    return render_template('settings.html', 
                         categories=data['categories'],
                         currencies=CURRENCIES,
                         current_currency=data['settings']['currency'],
                         current_theme=data['settings']['theme'])

@app.route('/delete_expense/<int:expense_id>')
def delete_expense(expense_id):
    """Delete an expense"""
    data = load_data()
    data['expenses'] = [exp for exp in data['expenses'] if exp['id'] != expense_id]
    save_data(data)
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('view_expenses'))

@app.route('/api/monthly_data')
def api_monthly_data():
    """API endpoint for chart data"""
    data = load_data()
    
    # Get last 12 months of data
    monthly_totals = defaultdict(float)
    for expense in data['expenses']:
        month = expense['date'][:7]
        monthly_totals[month] += expense['amount']
    
    # Format for charts
    chart_data = []
    for i in range(12):
        date = datetime.now() - timedelta(days=30*i)
        month_key = date.strftime('%Y-%m')
        month_name = date.strftime('%b %Y')
        chart_data.append({
            'month': month_name,
            'amount': monthly_totals.get(month_key, 0)
        })
    
    chart_data.reverse()
    return jsonify(chart_data)

@app.route('/goals', methods=['GET', 'POST'])
def financial_goals():
    """Manage financial goals"""
    data = load_data()
    
    if request.method == 'POST':
        goal = {
            'id': len(data['goals']) + 1,
            'title': request.form['title'],
            'target_amount': float(request.form['target_amount']),
            'current_amount': 0,
            'target_date': request.form['target_date'],
            'category': request.form.get('category', 'Savings'),
            'created_at': datetime.now().isoformat()
        }
        data['goals'].append(goal)
        save_data(data)
        flash('Financial goal added successfully!', 'success')
    
    currency = data['settings']['currency']
    return render_template('goals.html', 
                         goals=data['goals'],
                         categories=data['categories'],
                         currency_symbol=CURRENCIES[currency]['symbol'])

@app.route('/insights')
def insights():
    """Advanced spending insights"""
    data = load_data()
    
    # Calculate spending patterns
    weekly_spending = defaultdict(float)
    daily_spending = defaultdict(float)
    
    for expense in data['expenses']:
        date_obj = datetime.strptime(expense['date'], '%Y-%m-%d')
        week_key = date_obj.strftime('%Y-W%U')
        day_key = date_obj.strftime('%A')
        
        weekly_spending[week_key] += expense['amount']
        daily_spending[day_key] += expense['amount']
    
    # Calculate trends
    recent_expenses = [exp for exp in data['expenses'] 
                      if datetime.strptime(exp['date'], '%Y-%m-%d') >= datetime.now() - timedelta(days=30)]
    
    currency = data['settings']['currency']
    
    return render_template('insights.html',
                         weekly_spending=dict(weekly_spending),
                         daily_spending=dict(daily_spending),
                         recent_expenses=recent_expenses,
                         currency_symbol=CURRENCIES[currency]['symbol'])

@app.route('/help')
def help_page():
    """Help and onboarding page"""
    return render_template('help.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
