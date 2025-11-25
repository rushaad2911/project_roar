from django.contrib import admin
from .models import FeeCategory, FeeInvoice, FeeInvoiceItem, Payment

@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'is_recurring')
    search_fields = ('name', 'description')

class FeeInvoiceItemInline(admin.TabularInline):
    model = FeeInvoiceItem
    extra = 1

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('payment_date', 'receipt_number')

@admin.register(FeeInvoice)
class FeeInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'student', 'total_amount', 'paid_amount', 'balance', 'status', 'due_date')
    list_filter = ('status', 'issue_date', 'due_date')
    search_fields = ('invoice_number', 'student__user__first_name', 'student__user__last_name', 'student__student_id')
    readonly_fields = ('paid_amount', 'issue_date')
    inlines = [FeeInvoiceItemInline, PaymentInline]

    def balance(self, obj):
        return obj.balance
    balance.short_description = 'Balance'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'invoice', 'amount', 'payment_method', 'payment_date')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('receipt_number', 'transaction_id', 'invoice__invoice_number', 'invoice__student__user__first_name')
    readonly_fields = ('receipt_number', 'payment_date')