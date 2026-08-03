from django.contrib import admin
from .models import Category, Expense, Income

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'category', 'date', 'user', 'created_at')
    list_filter = ('category', 'date', 'user')
    search_fields = ('title', 'description', 'user__username')
    date_hierarchy = 'date'

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('source', 'amount', 'date', 'user', 'created_at')
    list_filter = ('date', 'user')
    search_fields = ('source', 'description', 'user__username')
    date_hierarchy = 'date'

