from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib import messages
from django.db.models import Sum, Max, Q
from django.utils import timezone
from django.http import JsonResponse
import datetime

from .models import Expense, Income, Category
from .forms import RegisterForm, ExpenseForm, IncomeForm, CategoryForm

from .signals import send_welcome_email, send_login_email

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_welcome_email(user)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            messages.success(request, f"Welcome to Expense Tracker, {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {'form': form})

@login_required
def dashboard_view(request):
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    # Calculations for user
    total_income = Income.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = Expense.objects.filter(user=request.user).aggregate(Sum('amount'))['amount__sum'] or 0
    current_balance = total_income - total_expense

    todays_expense = Expense.objects.filter(user=request.user, date=today).aggregate(Sum('amount'))['amount__sum'] or 0
    monthly_expense = Expense.objects.filter(
        user=request.user,
        date__year=current_year,
        date__month=current_month
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Recent transactions combining expenses and incomes
    recent_expenses = list(Expense.objects.filter(user=request.user).order_by('-date', '-created_at')[:5])
    recent_incomes = list(Income.objects.filter(user=request.user).order_by('-date', '-created_at')[:5])

    # Tag type for unified list
    for e in recent_expenses:
        e.tx_type = 'expense'
    for i in recent_incomes:
        i.tx_type = 'income'

    recent_transactions = sorted(
        recent_expenses + recent_incomes,
        key=lambda x: (x.date, getattr(x, 'created_at', timezone.now())),
        reverse=True
    )[:8]

    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'current_balance': current_balance,
        'todays_expense': todays_expense,
        'monthly_expense': monthly_expense,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'dashboard.html', context)

@login_required
def expense_list_view(request):
    expenses = Expense.objects.filter(user=request.user)
    categories = Category.objects.all()

    # Search query
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    filter_period = request.GET.get('period', '')
    min_amount = request.GET.get('min_amount', '')
    max_amount = request.GET.get('max_amount', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    if q:
        expenses = expenses.filter(Q(title__icontains=q) | Q(description__icontains=q))

    if category_id:
        expenses = expenses.filter(category_id=category_id)

    today = timezone.now().date()
    if filter_period == 'today':
        expenses = expenses.filter(date=today)
    elif filter_period == 'this_week':
        start_of_week = today - datetime.timedelta(days=today.weekday())
        expenses = expenses.filter(date__gte=start_of_week)
    elif filter_period == 'this_month':
        expenses = expenses.filter(date__year=today.year, date__month=today.month)
    elif filter_period == 'this_year':
        expenses = expenses.filter(date__year=today.year)

    if min_amount:
        try:
            expenses = expenses.filter(amount__gte=float(min_amount))
        except ValueError:
            pass

    if max_amount:
        try:
            expenses = expenses.filter(amount__lte=float(max_amount))
        except ValueError:
            pass

    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)

    context = {
        'expenses': expenses,
        'categories': categories,
        'q': q,
        'selected_category': category_id,
        'selected_period': filter_period,
        'min_amount': min_amount,
        'max_amount': max_amount,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'expenses.html', context)

@login_required
def expense_add_view(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, "Expense added successfully!")
            return redirect('expenses')
    else:
        form = ExpenseForm(initial={'date': timezone.now().date()})
    return render(request, 'add_expense.html', {'form': form, 'title': 'Add Expense'})

@login_required
def expense_edit_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense updated successfully!")
            return redirect('expenses')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'add_expense.html', {'form': form, 'title': 'Edit Expense', 'expense': expense})

@login_required
def expense_delete_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, "Expense deleted successfully!")
        return redirect('expenses')
    return render(request, 'expense_confirm_delete.html', {'expense': expense})

@login_required
def expense_detail_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    return render(request, 'expense_detail.html', {'expense': expense})

@login_required
def income_add_view(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            messages.success(request, "Income added successfully!")
            return redirect('dashboard')
    else:
        form = IncomeForm(initial={'date': timezone.now().date()})
    return render(request, 'add_income.html', {'form': form, 'title': 'Add Income'})

@login_required
def income_edit_view(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            form.save()
            messages.success(request, "Income updated successfully!")
            return redirect('dashboard')
    else:
        form = IncomeForm(instance=income)
    return render(request, 'add_income.html', {'form': form, 'title': 'Edit Income', 'income': income})

@login_required
def income_delete_view(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    if request.method == 'POST':
        income.delete()
        messages.success(request, "Income deleted successfully!")
        return redirect('dashboard')
    return render(request, 'income_confirm_delete.html', {'income': income})

@login_required
def reports_view(request):
    user_expenses = Expense.objects.filter(user=request.user)
    user_incomes = Income.objects.filter(user=request.user)

    total_expense = user_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    total_income = user_incomes.aggregate(Sum('amount'))['amount__sum'] or 0

    highest_expense = user_expenses.order_by('-amount').first()

    # Category-wise breakdown
    category_expenses = (
        user_expenses.values('category__name', 'category__icon')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    # Monthly breakdown for the past 6 months
    today = timezone.now().date()
    monthly_data = []
    for i in range(5, -1, -1):
        # Calculate month date offset
        year = today.year
        month = today.month - i
        if month <= 0:
            month += 12
            year -= 1
        m_exp = user_expenses.filter(date__year=year, date__month=month).aggregate(Sum('amount'))['amount__sum'] or 0
        m_inc = user_incomes.filter(date__year=year, date__month=month).aggregate(Sum('amount'))['amount__sum'] or 0
        month_name = datetime.date(year, month, 1).strftime('%b %Y')
        monthly_data.append({
            'month': month_name,
            'expense': float(m_exp),
            'income': float(m_inc)
        })

    context = {
        'total_expense': total_expense,
        'total_income': total_income,
        'highest_expense': highest_expense,
        'category_expenses': category_expenses,
        'monthly_data': monthly_data,
    }
    return render(request, 'reports.html', context)

@login_required
def chart_data_api(request):
    user_expenses = Expense.objects.filter(user=request.user)
    user_incomes = Income.objects.filter(user=request.user)

    # 1. Pie Chart: Expenses by Category
    cat_data = (
        user_expenses.values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    pie_labels = [item['category__name'] if item['category__name'] else 'Uncategorized' for item in cat_data]
    pie_values = [float(item['total']) for item in cat_data]

    # 2. Bar Chart & Line Chart: Last 6 Months Trends
    today = timezone.now().date()
    months_labels = []
    monthly_expenses = []
    monthly_incomes = []

    for i in range(5, -1, -1):
        year = today.year
        month = today.month - i
        if month <= 0:
            month += 12
            year -= 1
        m_exp = user_expenses.filter(date__year=year, date__month=month).aggregate(Sum('amount'))['amount__sum'] or 0
        m_inc = user_incomes.filter(date__year=year, date__month=month).aggregate(Sum('amount'))['amount__sum'] or 0
        months_labels.append(datetime.date(year, month, 1).strftime('%b %Y'))
        monthly_expenses.append(float(m_exp))
        monthly_incomes.append(float(m_inc))

    return JsonResponse({
        'pie': {
            'labels': pie_labels,
            'values': pie_values,
        },
        'bar': {
            'labels': months_labels,
            'expenses': monthly_expenses,
            'incomes': monthly_incomes,
        },
        'line': {
            'labels': months_labels,
            'expenses': monthly_expenses,
        }
    })

import io
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_report(user, year=None, month=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    elements = []

    today = timezone.now().date()
    if not year or not month:
        year = today.year
        month = today.month

    month_name = datetime.date(year, month, 1).strftime('%B %Y')

    # Data calculations
    user_expenses = Expense.objects.filter(user=user, date__year=year, date__month=month)
    user_incomes = Income.objects.filter(user=user, date__year=year, date__month=month)

    total_expense = user_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    total_income = user_incomes.aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_income - total_expense
    highest_expense = user_expenses.order_by('-amount').first()

    # Category breakdown
    category_expenses = (
        user_expenses.values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b')
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1e293b'),
        fontName='Helvetica-Bold',
        spaceBefore=14,
        spaceAfter=6
    )

    # Document Header
    elements.append(Paragraph("EXPENZA - FINANCIAL REPORT", title_style))
    elements.append(Paragraph(f"User: {user.get_full_name() or user.username} ({user.email}) | Period: {month_name}", subtitle_style))
    elements.append(Spacer(1, 10))

    # Summary Table
    summary_data = [
        ["Total Income", "Total Expense", "Net Balance", "Highest Expense"],
        [
            f"INR {total_income:,.2f}",
            f"INR {total_expense:,.2f}",
            f"INR {balance:,.2f}",
            f"INR {highest_expense.amount:,.2f}" if highest_expense else "N/A"
        ]
    ]
    summary_table = Table(summary_data, colWidths=[130, 130, 130, 150])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#ef4444')),
        ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#6366f1')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 10))

    # Category Breakdown
    elements.append(Paragraph("Category Spending Breakdown", section_heading))
    cat_data = [["Category", "Total Spent", "Percentage"]]
    for cat in category_expenses:
        cat_name = cat['category__name'] or "Uncategorized"
        cat_total = cat['total'] or 0
        pct = (cat_total / total_expense * 100) if total_expense > 0 else 0
        cat_data.append([cat_name, f"INR {cat_total:,.2f}", f"{pct:.1f}%"])
    if len(cat_data) == 1:
        cat_data.append(["No expenses recorded", "INR 0.00", "0%"])

    cat_table = Table(cat_data, colWidths=[240, 150, 150])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(cat_table)
    elements.append(Spacer(1, 10))

    # Transaction Log
    elements.append(Paragraph("Itemized Transactions Log", section_heading))
    tx_expenses = list(user_expenses)
    tx_incomes = list(user_incomes)
    for e in tx_expenses: e.tx_type = 'Expense'
    for i in tx_incomes: i.tx_type = 'Income'

    all_txs = sorted(tx_expenses + tx_incomes, key=lambda x: x.date, reverse=True)
    tx_data = [["Type", "Date", "Title / Source", "Category", "Amount"]]

    cell_style = ParagraphStyle('CellText', parent=styles['Normal'], fontSize=8, leading=10)

    for tx in all_txs[:50]:
        cat_str = getattr(tx, 'category', None)
        cat_name = cat_str.name if cat_str else '-'
        title_str = getattr(tx, 'title', getattr(tx, 'source', ''))
        amount_str = f"+INR {tx.amount:,.2f}" if tx.tx_type == 'Income' else f"-INR {tx.amount:,.2f}"
        tx_data.append([
            tx.tx_type,
            tx.date.strftime('%Y-%m-%d'),
            Paragraph(title_str, cell_style),
            cat_name,
            amount_str
        ])

    if len(tx_data) == 1:
        tx_data.append(["-", "-", "No transactions found", "-", "INR 0.00"])

    tx_table = Table(tx_data, colWidths=[65, 75, 180, 100, 120])
    tx_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(tx_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

@login_required
def download_report_pdf_view(request):
    today = timezone.now().date()
    year = request.GET.get('year', today.year)
    month = request.GET.get('month', today.month)

    try:
        year = int(year)
        month = int(month)
    except ValueError:
        year = today.year
        month = today.month

    pdf_bytes = generate_pdf_report(request.user, year=year, month=month)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"expense_report_{year}_{month:02d}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: u.is_staff)
def admin_dashboard_view(request):
    total_users = User.objects.count()
    total_categories = Category.objects.count()
    total_expenses = Expense.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    total_incomes = Income.objects.aggregate(Sum('amount'))['amount__sum'] or 0

    users_list = User.objects.all().order_by('-date_joined')
    categories_list = Category.objects.all()
    all_expenses = Expense.objects.select_related('user', 'category').all()[:25]
    category_form = CategoryForm()

    context = {
        'total_users': total_users,
        'total_categories': total_categories,
        'total_expenses': total_expenses,
        'total_incomes': total_incomes,
        'users_list': users_list,
        'categories_list': categories_list,
        'all_expenses': all_expenses,
        'category_form': category_form,
    }
    return render(request, 'admin_dashboard.html', context)

@user_passes_test(lambda u: u.is_staff)
def admin_category_add_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Category '{cat.name}' added successfully!")
        else:
            messages.error(request, "Failed to add category. Please check inputs.")
    return redirect('admin_dashboard')


