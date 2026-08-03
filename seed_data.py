import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'expense_tracker.settings')
django.setup()

from expenses.models import Category
from django.contrib.sites.models import Site

site, created = Site.objects.get_or_create(id=1)
site.domain = '127.0.0.1:8000'
site.name = 'Expense Tracker'
site.save()
print(f"Updated Site: {site.domain}")

DEFAULT_CATEGORIES = [
    {'name': 'Food', 'icon': 'fas fa-utensils'},
    {'name': 'Travel', 'icon': 'fas fa-plane'},
    {'name': 'Shopping', 'icon': 'fas fa-shopping-bag'},
    {'name': 'Medical', 'icon': 'fas fa-user-md'},
    {'name': 'Education', 'icon': 'fas fa-graduation-cap'},
    {'name': 'Bills', 'icon': 'fas fa-file-invoice-dollar'},
    {'name': 'Entertainment', 'icon': 'fas fa-film'},
]

for cat_data in DEFAULT_CATEGORIES:
    cat, created = Category.objects.get_or_create(
        name=cat_data['name'],
        defaults={'icon': cat_data['icon']}
    )
    if created:
        print(f"Created category: {cat.name}")
    else:
        print(f"Category already exists: {cat.name}")

from django.contrib.auth.models import User

# Superuser Setup
admin_username = 'admin'
admin_email = 'expensetracker@gmail.com'
admin_pass = 'Admin@1234'

if not User.objects.filter(username=admin_username).exists():
    admin_user = User.objects.create_superuser(
        username=admin_username,
        email=admin_email,
        password=admin_pass
    )
    admin_user.first_name = "Admin"
    admin_user.save()
    print(f"Created Admin Superuser: {admin_username} ({admin_email})")
else:
    admin_user = User.objects.get(username=admin_username)
    admin_user.email = admin_email
    admin_user.set_password(admin_pass)
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()
    print(f"Updated Admin Superuser credentials: {admin_username} ({admin_email})")

print("Category, Site, and Admin Superuser seeding completed!")


