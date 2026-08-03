import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.utils import timezone
from django.db.models import Sum
from expenses.models import Expense, Income
from expenses.views import generate_pdf_report

class Command(BaseCommand):
    help = 'Sends end-of-month financial PDF reports to all registered users via email.'

    def handle(self, *args, **options):
        today = timezone.now().date()
        year = today.year
        month = today.month

        month_str = datetime.date(year, month, 1).strftime('%B %Y')
        users = User.objects.filter(is_active=True).exclude(email='')

        if not users.exists():
            self.stdout.write(self.style.WARNING("No active users with registered email addresses found."))
            return

        sent_count = 0
        for user in users:
            pdf_data = generate_pdf_report(user, year=year, month=month)

            total_expense = Expense.objects.filter(user=user, date__year=year, date__month=month).aggregate(
                total=Sum('amount')
            )['total'] or 0
            total_income = Income.objects.filter(user=user, date__year=year, date__month=month).aggregate(
                total=Sum('amount')
            )['total'] or 0
            balance = total_income - total_expense

            subject = f"Your Monthly Financial Report for {month_str} - Expenza"
            body = (
                f"Hello {user.first_name or user.username},\n\n"
                f"Here is your financial summary for {month_str}:\n\n"
                f"• Total Income: INR {total_income:,.2f}\n"
                f"• Total Expense: INR {total_expense:,.2f}\n"
                f"• Net Balance: INR {balance:,.2f}\n\n"
                f"Please find your complete detailed PDF report attached to this email.\n\n"
                f"Thank you for using Expenza!\n"
            )

            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=None,
                to=[user.email]
            )
            filename = f"expense_report_{year}_{month:02d}.pdf"
            email.attach(filename, pdf_data, 'application/pdf')
            
            try:
                email.send()
                sent_count += 1
                self.stdout.write(self.style.SUCCESS(f"Successfully sent monthly PDF report to {user.email}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to send email to {user.email}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Monthly report dispatch finished. Total emails sent: {sent_count}"))
