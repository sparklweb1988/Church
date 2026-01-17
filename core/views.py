from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django. contrib import messages
from django.contrib.auth.models import User
from . models import Financial
from django.utils.dateparse import parse_date
from django.http import HttpResponse
from openpyxl import Workbook
import openpyxl





def signin_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('pw')

        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('transaction')
    return render(request, 'signin.html')







def transaction(request):
    all_transactions = Financial.objects.all().order_by('-created_at')
    transactions = all_transactions

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        parsed_from = parse_date(from_date)
        if parsed_from:
            transactions = transactions.filter(created_at__gte=parsed_from)

    if to_date:
        parsed_to = parse_date(to_date)
        if parsed_to:
            transactions = transactions.filter(created_at__lte=parsed_to)

    # Calculate grand total using Python property
    grand_total = sum(t.total for t in transactions)

    context = {
        'transactions': transactions,
        'all_transactions': all_transactions,
        'grand_total': grand_total,
        'from_date': from_date,
        'to_date': to_date,
    }

    return render(request, "transaction.html", context)




def transaction_percentages(request):
    # Start with all transactions
    transactions = Financial.objects.all().order_by('-created_at')

    # --- Date filters ---
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        parsed_from = parse_date(from_date)
        if parsed_from:
            transactions = transactions.filter(created_at__gte=parsed_from)

    if to_date:
        parsed_to = parse_date(to_date)
        if parsed_to:
            transactions = transactions.filter(created_at__lte=parsed_to)

    # --- Compute weighted totals and individual percentages ---
    for t in transactions:
        t.crm_pct_val = t.crm_pct
        t.general_tithe_pct_val = t.general_tithe_pct
        t.minister_tithe_pct_val = t.minister_tithe_pct
        t.sunday_school_pct_val = t.sunday_school_pct
        t.thanksgiving_pct_val = t.thanksgiving_pct
        t.children_pct_val = t.children_pct
        t.weighted_total_val = t.weighted_total

    # --- Grand totals ---
    grand_weighted_total = sum(t.weighted_total_val for t in transactions)
    grand_total = sum(t.total for t in transactions)

    context = {
        'transactions': transactions,
        'grand_weighted_total': grand_weighted_total,
        'grand_total': grand_total,
        'from_date': from_date,
        'to_date': to_date,
    }

    return render(request, "percentages.html", context)














from datetime import date

def transaction_summary(request):
    # Start with all transactions
    transactions = Financial.objects.all().order_by('-created_at')

    # Get date filters from GET parameters
    from_date = request.GET.get('from_date', str(date.today()))  # Default to today if not provided
    to_date = request.GET.get('to_date', str(date.today()))  # Default to today if not provided

    # Convert from string to date
    from_date_parsed = parse_date(from_date)
    to_date_parsed = parse_date(to_date)

    # Filter by 'from_date' if provided
    if from_date_parsed:
        transactions = transactions.filter(created_at__gte=from_date_parsed)

    # Filter by 'to_date' if provided
    if to_date_parsed:
        transactions = transactions.filter(created_at__lte=to_date_parsed)

    # Aggregate data
    transaction_count = transactions.count()
    grand_total = sum([t.total or 0 for t in transactions])

    # Optional: Calculate additional statistics like average transaction value
    average_transaction = grand_total / transaction_count if transaction_count else 0

    context = {
        'transaction_count': transaction_count,
        'grand_total': grand_total,
        'average_transaction': average_transaction,
        'from_date': from_date,
        'to_date': to_date,
    }

    return render(request, 'transaction_summary.html', context)





# Add new financial record
def add_financial(request):
    if request.method == "POST":
        def get_decimal(field_name):
            """Helper: convert empty POST values to 0"""
            value = request.POST.get(field_name)
            return float(value) if value else 0  # use 0 for empty fields

        Financial.objects.create(
            user=request.user,  # automatically assign logged-in user
            crm=get_decimal("crm"),
            offering=get_decimal("offering"),
            minister_tithe=get_decimal("minister_tithe"),
            general_tithe=get_decimal("general_tithe"),
            thanksgiving=get_decimal("thanksgiving"),
            breakthrough=get_decimal("breakthrough"),
            others=get_decimal("others"),
            sunday_school=get_decimal("sunday_school"),
            children=get_decimal("children"),
        )
        return redirect('transaction')  # redirect to your transactions page

    return render(request, 'financial_form.html', {'action': 'Add'})




# Edit existing financial record
def edit_financial(request, pk):
    financial = get_object_or_404(Financial, pk=pk)

    if request.method == "POST":
        financial.crm = request.POST.get("crm", 0)
        financial.offering = request.POST.get("offering", 0)
        financial.minister_tithe = request.POST.get("minister_tithe", 0)
        financial.general_tithe = request.POST.get("general_tithe", 0)
        financial.thanksgiving = request.POST.get("thanksgiving", 0)
        financial.breakthrough = request.POST.get("breakthrough", 0)
        financial.others = request.POST.get("others", 0)
        financial.sunday_school = request.POST.get("sunday_school", 0)
        financial.children = request.POST.get("children", 0)
        financial.save()
        return redirect('transaction')  # redirect to transactions page

    return render(request, 'financial_form.html', {'financial': financial, 'action': 'Edit'})



# Delete a financial record
def delete_financial(request, pk):
    financial = get_object_or_404(Financial, pk=pk)
    financial.delete()
    return redirect('transaction')










def export_transactions_excel(request):
    # Filter transactions same as your transaction view
    transactions = Financial.objects.all().order_by('-created_at')

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        from_date_parsed = parse_date(from_date)
        if from_date_parsed:
            transactions = transactions.filter(created_at__gte=from_date_parsed)

    if to_date:
        to_date_parsed = parse_date(to_date)
        if to_date_parsed:
            transactions = transactions.filter(created_at__lte=to_date_parsed)

    # Calculate grand total across all numeric fields
    grand_total = 0
    for t in transactions:
        row_total = sum([
            t.crm or 0, t.offering or 0, t.minister_tithe or 0, t.general_tithe or 0,
            t.thanksgiving or 0, t.breakthrough or 0, t.others or 0, t.sunday_school or 0, t.children or 0
        ])
        grand_total += row_total

    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Transactions"

    # Header row
    headers = ["ID", "Date", "CRM", "Offering", "Minister Tithe", "General Tithe",
               "Thanksgiving", "Breakthrough", "Others", "Sunday School", "Children", "Total"]
    ws.append(headers)

    # Fill transaction rows
    for t in transactions:
        row = [
            t.id,
            t.created_at.strftime("%Y-%m-%d"),
            t.crm or 0,
            t.offering or 0,
            t.minister_tithe or 0,
            t.general_tithe or 0,
            t.thanksgiving or 0,
            t.breakthrough or 0,
            t.others or 0,
            t.sunday_school or 0,
            t.children or 0,
            sum([
                t.crm or 0, t.offering or 0, t.minister_tithe or 0, t.general_tithe or 0,
                t.thanksgiving or 0, t.breakthrough or 0, t.others or 0, t.sunday_school or 0, t.children or 0
            ])
        ]
        ws.append(row)

    # Add grand total row at the bottom
    ws.append([])  # empty row
    ws.append(["", "", "", "", "", "", "", "", "", "", "Grand Total:", grand_total])

    # Prepare response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=transactions.xlsx'
    wb.save(response)
    return response








def returns_summary(request):
    # Start with all transactions, ordered by newest first
    transactions = Financial.objects.all().order_by('-created_at')

    # --- Date filters ---
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        parsed_from = parse_date(from_date)
        if parsed_from:
            transactions = transactions.filter(created_at__gte=parsed_from)

    if to_date:
        parsed_to = parse_date(to_date)
        if parsed_to:
            transactions = transactions.filter(created_at__lte=parsed_to)

    # --- Initialize Decimal sums ---
    total_general_tithe = Decimal('0')
    total_minister_tithe = Decimal('0')
    total_sunday_school = Decimal('0')
    total_thanksgiving = Decimal('0')
    total_crm = Decimal('0')
    total_children = Decimal('0')
    grand_total = Decimal('0')

    # --- Compute sums for weighted totals ---
    for t in transactions:
        total_general_tithe += t.general_tithe_pct
        total_minister_tithe += t.minister_tithe_pct
        total_sunday_school += t.sunday_school_pct
        total_thanksgiving += t.thanksgiving_pct
        total_crm += t.crm_pct
        total_children += t.children_pct
        grand_total += t.weighted_total

    # --- Prepare summary dictionary ---
    summary = {
        'general_tithe': total_general_tithe,
        'minister_tithe': total_minister_tithe,
        'sunday_school': total_sunday_school,
        'thanksgiving': total_thanksgiving,
        'crm': total_crm,
        'children': total_children,
        'grand_total': grand_total,
    }

    # --- Compute actual amounts (100%) safely ---
    actual_amounts = {
        'general_tithe': (total_general_tithe / Decimal('0.64')) if total_general_tithe else Decimal('0'),
        'minister_tithe': (total_minister_tithe / Decimal('0.64')) if total_minister_tithe else Decimal('0'),
        'sunday_school': (total_sunday_school / Decimal('0.50')) if total_sunday_school else Decimal('0'),
        'thanksgiving': (total_thanksgiving / Decimal('0.70')) if total_thanksgiving else Decimal('0'),
        'crm': (total_crm / Decimal('0.50')) if total_crm else Decimal('0'),
        'children': (total_children / Decimal('0.35')) if total_children else Decimal('0'),
    }

    context = {
        'summary': summary,
        'actual_amounts': actual_amounts,
        'from_date': from_date,
        'to_date': to_date,
    }

    return render(request, 'percentages.html', context)







def export_returns_summary(request):
    # Fetch all transactions
    transactions = Financial.objects.all().order_by('-created_at')

    # --- Date filters ---
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        parsed_from = parse_date(from_date)
        if parsed_from:
            transactions = transactions.filter(created_at__gte=parsed_from)

    if to_date:
        parsed_to = parse_date(to_date)
        if parsed_to:
            transactions = transactions.filter(created_at__lte=parsed_to)

    # --- Compute totals using Decimal ---
    total_general_tithe = Decimal('0')
    total_minister_tithe = Decimal('0')
    total_sunday_school = Decimal('0')
    total_thanksgiving = Decimal('0')
    total_crm = Decimal('0')
    total_children = Decimal('0')
    grand_total = Decimal('0')

    for t in transactions:
        total_general_tithe += t.general_tithe_pct
        total_minister_tithe += t.minister_tithe_pct
        total_sunday_school += t.sunday_school_pct
        total_thanksgiving += t.thanksgiving_pct
        total_crm += t.crm_pct
        total_children += t.children_pct
        grand_total += t.weighted_total

    # --- Calculate actual amounts (100%) safely ---
    actual_amounts = {
        'general_tithe': (total_general_tithe / Decimal('0.64')) if total_general_tithe else Decimal('0'),
        'minister_tithe': (total_minister_tithe / Decimal('0.64')) if total_minister_tithe else Decimal('0'),
        'sunday_school': (total_sunday_school / Decimal('0.50')) if total_sunday_school else Decimal('0'),
        'thanksgiving': (total_thanksgiving / Decimal('0.70')) if total_thanksgiving else Decimal('0'),
        'crm': (total_crm / Decimal('0.50')) if total_crm else Decimal('0'),
        'children': (total_children / Decimal('0.35')) if total_children else Decimal('0'),
    }

    # --- Create Excel response ---
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="returns_summary.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Returns Summary'

    # --- Headers ---
    ws.append(['Item Name', 'Actual Amount (100%)', 'Percentage', 'Total Value'])

    # --- Data rows ---
    data = [
        ('General Tithe', actual_amounts['general_tithe'], '64%', total_general_tithe),
        ('Minister Tithe', actual_amounts['minister_tithe'], '64%', total_minister_tithe),
        ('Sunday School', actual_amounts['sunday_school'], '50%', total_sunday_school),
        ('Thanksgiving', actual_amounts['thanksgiving'], '70%', total_thanksgiving),
        ('CRM', actual_amounts['crm'], '50%', total_crm),
        ('Children', actual_amounts['children'], '35%', total_children),
    ]

    for row in data:
        ws.append(row)

    # --- Grand total row ---
    ws.append(['Grand Total', '', '', grand_total])

    wb.save(response)
    return response






def logout_view(request):
    logout(request)
    messages.success(request, ' Logout successfully')
    return redirect('login')
