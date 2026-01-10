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
    # Start with all transactions
    transactions = Financial.objects.all().order_by('-created_at')  # Most recent first

    # Get date filters from GET parameters
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # Debugging: Print the dates to verify if they're being passed correctly
    print(f"From Date: {from_date}")
    print(f"To Date: {to_date}")

    # Filter by 'from_date' if provided
    if from_date:
        from_date_parsed = parse_date(from_date)
        if from_date_parsed:
            transactions = transactions.filter(created_at__gte=from_date_parsed)

    # Filter by 'to_date' if provided
    if to_date:
        to_date_parsed = parse_date(to_date)
        if to_date_parsed:
            transactions = transactions.filter(created_at__lte=to_date_parsed)

    # Safely calculate grand total, treating None as 0
    grand_total = sum([t.total or 0 for t in transactions])

    # Context to pass to template
    context = {
        'transactions': transactions,
        'grand_total': grand_total,
        'from_date': from_date,
        'to_date': to_date,
    }

    return render(request, 'transaction.html', context)






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
    transactions = Financial.objects.all()

    # Optional: filter by date
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        parsed = parse_date(from_date)
        if parsed:
            transactions = transactions.filter(created_at__gte=parsed)
    if to_date:
        parsed = parse_date(to_date)
        if parsed:
            transactions = transactions.filter(created_at__lte=parsed)

    # Aggregate totals for each field
    summary = {
        'general_tithe': sum(t.general_tithe_pct for t in transactions),
        'minister_tithe': sum(t.minister_tithe_pct for t in transactions),
        'sunday_school': sum(t.sunday_school_pct for t in transactions),
        'thanksgiving': sum(t.thanksgiving_pct for t in transactions),
        'crm': sum(t.crm_pct for t in transactions),
        'children': sum(t.children_pct for t in transactions),
        'grand_total': sum(t.weighted_total for t in transactions),
    }

    # Calculate Actual Amount (100%) for each field
    actual_amounts = {
        'general_tithe': summary['general_tithe'] / 0.64 if summary['general_tithe'] else 0,
        'minister_tithe': summary['minister_tithe'] / 0.64 if summary['minister_tithe'] else 0,
        'sunday_school': summary['sunday_school'] / 0.50 if summary['sunday_school'] else 0,
        'thanksgiving': summary['thanksgiving'] / 0.70 if summary['thanksgiving'] else 0,
        'crm': summary['crm'] / 0.50 if summary['crm'] else 0,
        'children': summary['children'] / 0.35 if summary['children'] else 0,
    }

    context = {
        'summary': summary,
        'actual_amounts': actual_amounts,
        'from_date': from_date,
        'to_date': to_date,
    }
    return render(request, 'percentages.html', context)



def export_returns_summary(request):
    # Fetch the summary data
    transactions = Financial.objects.all()

    # Filter data by date if present
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        parsed = parse_date(from_date)
        if parsed:
            transactions = transactions.filter(created_at__gte=parsed)
    if to_date:
        parsed = parse_date(to_date)
        if parsed:
            transactions = transactions.filter(created_at__lte=parsed)

    # Calculate the summary
    summary = {
        'general_tithe': sum(t.general_tithe_pct for t in transactions),
        'minister_tithe': sum(t.minister_tithe_pct for t in transactions),
        'sunday_school': sum(t.sunday_school_pct for t in transactions),
        'thanksgiving': sum(t.thanksgiving_pct for t in transactions),
        'crm': sum(t.crm_pct for t in transactions),
        'children': sum(t.children_pct for t in transactions),
        'grand_total': sum(t.weighted_total for t in transactions),
    }

    # Create an Excel response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="returns_summary.xlsx"'

    # Create a workbook and a worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Returns Summary'

    # Add headers to the Excel file
    headers = ['Item Name', 'Actual Amount (100%)', 'Percentage', 'Total Value']
    ws.append(headers)

    # Data to be written
    data = [
        ('General Tithe', summary['general_tithe'] / 0.64, '64%', summary['general_tithe']),
        ('Minister Tithe', summary['minister_tithe'] / 0.64, '64%', summary['minister_tithe']),
        ('Sunday School', summary['sunday_school'] / 0.50, '50%', summary['sunday_school']),
        ('Thanksgiving', summary['thanksgiving'] / 0.70, '70%', summary['thanksgiving']),
        ('CRM', summary['crm'] / 0.50, '50%', summary['crm']),
        ('Children', summary['children'] / 0.35, '35%', summary['children']),
    ]

    # Write the data to the Excel sheet
    for item in data:
        ws.append(item)

    # Write the grand total at the end
    ws.append(['Grand Total', '', '', summary['grand_total']])

    # Save the workbook to the response object
    wb.save(response)
    return response



def logout_view(request):
    logout(request)
    messages.success(request, ' Logout successfully')
    return redirect('login')