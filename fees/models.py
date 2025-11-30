import uuid
from django.db import models
from students.models import Student

class FeeCategory(models.Model):
    """
    Model for storing different fee categories (e.g., Tuition, Library, etc.)
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_recurring = models.BooleanField(default=True, help_text='Whether this fee is charged regularly')

    def __str__(self):
        return f"{self.name} (₹{self.amount})"

    class Meta:
        verbose_name_plural = 'Fee Categories'

class FeeInvoice(models.Model):
    """
    Model for storing fee invoices for students.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    )

    invoice_number = models.CharField(max_length=20, unique=True, default=uuid.uuid4)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_invoices')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateField()
    issue_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.student}"

    @property
    def balance(self):
        return self.total_amount - self.paid_amount

    @property
    def is_paid(self):
        return self.status == 'paid'

    class Meta:
        ordering = ['-issue_date']

class FeeInvoiceItem(models.Model):
    """
    Model for storing individual items in a fee invoice.
    """
    invoice = models.ForeignKey(FeeInvoice, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.category.name} - ₹{self.amount}"

class Payment(models.Model):
    """
    Model for storing payment records.
    """
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('other', 'Other'),
    )

    invoice = models.ForeignKey(FeeInvoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    receipt_number = models.CharField(max_length=20, unique=True, default=uuid.uuid4)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Payment of ₹{self.amount} for {self.invoice}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Update the invoice paid amount and status
        invoice = self.invoice
        total_paid = sum(payment.amount for payment in invoice.payments.all())
        invoice.paid_amount = total_paid

        if total_paid >= invoice.total_amount:
            invoice.status = 'paid'
        elif invoice.status == 'paid':
            invoice.status = 'pending'

        invoice.save()

    class Meta:
        ordering = ['-payment_date']