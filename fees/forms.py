from django import forms
from django.forms import inlineformset_factory
from .models import FeeCategory, FeeInvoice, FeeInvoiceItem, Payment

class FeeCategoryForm(forms.ModelForm):
    """
    Form for creating and updating fee categories.
    """
    class Meta:
        model = FeeCategory
        fields = ['name', 'description', 'amount', 'is_recurring']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

class FeeInvoiceForm(forms.ModelForm):
    """
    Form for creating and updating fee invoices.
    """
    class Meta:
        model = FeeInvoice
        fields = ['student', 'total_amount', 'due_date', 'status', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

class FeeInvoiceItemForm(forms.ModelForm):
    """
    Form for creating and updating fee invoice items.
    """
    class Meta:
        model = FeeInvoiceItem
        fields = ['category', 'amount', 'description']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

# Create a formset for fee invoice items
FeeInvoiceItemFormSet = inlineformset_factory(
    FeeInvoice, 
    FeeInvoiceItem, 
    form=FeeInvoiceItemForm,
    extra=1,
    can_delete=True
)

class PaymentForm(forms.ModelForm):
    """
    Form for creating payments.
    """
    class Meta:
        model = Payment
        fields = ['invoice', 'amount', 'payment_method', 'transaction_id', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

class PaymentCreateForm(forms.ModelForm):
    """
    Form for creating payments for a specific invoice.
    """
    class Meta:
        model = Payment
        fields = ['amount', 'payment_method', 'transaction_id', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
