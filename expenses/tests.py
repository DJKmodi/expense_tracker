from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from expenses.models import Category, Expense, Income

class ExpenseTrackerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123', first_name='Dhairya')
        self.category = Category.objects.create(name='Food', icon='fas fa-utensils')
        self.client = Client()

    def test_model_creation(self):
        expense = Expense.objects.create(
            user=self.user,
            title='Lunch',
            amount=25.50,
            category=self.category,
            date=timezone.now().date()
        )
        income = Income.objects.create(
            user=self.user,
            source='Salary',
            amount=1000.00,
            date=timezone.now().date()
        )
        self.assertEqual(str(expense), 'Lunch - ₹25.5')
        self.assertEqual(str(income), 'Salary - ₹1000.0')


    def test_dashboard_access_authenticated(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome, Dhairya')

    def test_expense_crud(self):
        self.client.login(username='testuser', password='password123')
        
        # Create expense
        response = self.client.post(reverse('expense_add'), {
            'title': 'Dinner',
            'amount': '45.00',
            'date': timezone.now().date().strftime('%Y-%m-%d'),
            'category': self.category.id,
            'description': 'Team dinner'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Expense.objects.filter(title='Dinner').exists())

        expense = Expense.objects.get(title='Dinner')
        
        # View expense detail
        detail_response = self.client.get(reverse('expense_detail', args=[expense.id]))
        self.assertEqual(detail_response.status_code, 200)

        # Edit expense
        edit_response = self.client.post(reverse('expense_edit', args=[expense.id]), {
            'title': 'Fancy Dinner',
            'amount': '60.00',
            'date': timezone.now().date().strftime('%Y-%m-%d'),
            'category': self.category.id,
            'description': 'Updated description'
        })
        self.assertEqual(edit_response.status_code, 302)
        expense.refresh_from_db()
        self.assertEqual(expense.title, 'Fancy Dinner')

        # Delete expense
        delete_response = self.client.post(reverse('expense_delete', args=[expense.id]))
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(Expense.objects.filter(title='Fancy Dinner').exists())

    def test_search_and_filter(self):
        self.client.login(username='testuser', password='password123')
        Expense.objects.create(user=self.user, title='Groceries', amount=100, date=timezone.now().date(), category=self.category)
        
        # Search query
        res = self.client.get(reverse('expenses') + '?q=Groceries')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Groceries')

        # Period filter
        res_filter = self.client.get(reverse('expenses') + '?period=today')
        self.assertEqual(res_filter.status_code, 200)
        self.assertContains(res_filter, 'Groceries')

    def test_chart_api(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('chart_data_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('pie', data)
        self.assertIn('bar', data)
        self.assertIn('line', data)

    def test_greeting_emails(self):
        from django.core import mail
        # Registration email
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        })
        self.assertEqual(response.status_code, 302)
        # Outbox should have emails sent (welcome + login)
        self.assertTrue(len(mail.outbox) >= 1)
        self.assertIn("Welcome to Expenza", mail.outbox[0].subject)

