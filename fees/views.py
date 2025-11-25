from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from .forms import FeeCategoryForm, FeeInvoiceForm, FeeInvoiceItemFormSet, PaymentForm, PaymentCreateForm
from .models import FeeCategory, FeeInvoice, FeeInvoiceItem, Payment
from students.models import Student
from students.views import AdminRequiredMixin

# Fee Category Views
class FeeCategoryListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """View to list all fee categories."""
    model = FeeCategory
    template_name = 'fees/fee_category_list.html'
    context_object_name = 'categories'

class FeeCategoryCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """View to create a new fee category."""
    model = FeeCategory
    form_class = FeeCategoryForm
    template_name = 'fees/fee_category_form.html'
    success_url = reverse_lazy('fee_category_list')

class FeeCategoryUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """View to update a fee category."""
    model = FeeCategory
    form_class = FeeCategoryForm
    template_name = 'fees/fee_category_form.html'
    success_url = reverse_lazy('fee_category_list')

class FeeCategoryDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """View to delete a fee category."""
    model = FeeCategory
    template_name = 'fees/fee_category_confirm_delete.html'
    success_url = reverse_lazy('fee_category_list')

# Fee Invoice Views
class FeeInvoiceListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """View to list all fee invoices."""
    model = FeeInvoice
    template_name = 'fees/fee_invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 10

class FeeInvoiceDetailView(LoginRequiredMixin, DetailView):
    """View to display fee invoice details."""
    model = FeeInvoice
    template_name = 'fees/fee_invoice_detail.html'
    context_object_name = 'invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['payments'] = self.object.payments.all()
        return context

class FeeInvoiceCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """View to create a new fee invoice."""
    model = FeeInvoice
    form_class = FeeInvoiceForm
    template_name = 'fees/fee_invoice_form.html'
    success_url = reverse_lazy('fee_invoice_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['items_formset'] = FeeInvoiceItemFormSet(self.request.POST)
        else:
            context['items_formset'] = FeeInvoiceItemFormSet()
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context['items_formset']

        if form.is_valid() and items_formset.is_valid():
            self.object = form.save()
            items_formset.instance = self.object
            items_formset.save()

            # Calculate total amount from items
            total = sum(item.amount for item in self.object.items.all())
            self.object.total_amount = total
            self.object.save()

            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class FeeInvoiceUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    """View to update a fee invoice."""
    model = FeeInvoice
    form_class = FeeInvoiceForm
    template_name = 'fees/fee_invoice_form.html'
    success_url = reverse_lazy('fee_invoice_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['items_formset'] = FeeInvoiceItemFormSet(self.request.POST, instance=self.object)
        else:
            context['items_formset'] = FeeInvoiceItemFormSet(instance=self.object)
        return context

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        items_formset = context['items_formset']

        if form.is_valid() and items_formset.is_valid():
            self.object = form.save()
            items_formset.instance = self.object
            items_formset.save()

            # Calculate total amount from items
            total = sum(item.amount for item in self.object.items.all())
            self.object.total_amount = total
            self.object.save()

            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class FeeInvoiceDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    """View to delete a fee invoice."""
    model = FeeInvoice
    template_name = 'fees/fee_invoice_confirm_delete.html'
    success_url = reverse_lazy('fee_invoice_list')

# Payment Views
class PaymentListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    """View to list all payments."""
    model = Payment
    template_name = 'fees/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 10

class PaymentCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """View to create a new payment."""
    model = Payment
    form_class = PaymentForm
    template_name = 'fees/payment_form.html'
    success_url = reverse_lazy('payment_list')

@login_required
def create_payment_for_invoice(request, invoice_id):
    """View to create a payment for a specific invoice."""
    invoice = get_object_or_404(FeeInvoice, pk=invoice_id)

    if request.method == 'POST':
        form = PaymentCreateForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()
            return redirect('fee_invoice_detail', pk=invoice.pk)
    else:
        form = PaymentCreateForm()

    return render(request, 'fees/payment_form.html', {
        'form': form,
        'invoice': invoice,
    })

class StudentFeeListView(LoginRequiredMixin, ListView):
    """View for students to see their fee invoices."""
    model = FeeInvoice
    template_name = 'fees/student_fee_list.html'
    context_object_name = 'invoices'

    def get_queryset(self):
        if self.request.user.is_student:
            try:
                student = Student.objects.get(user=self.request.user)
            except Student.DoesNotExist:
                student = None
            except Student.MultipleObjectsReturned:
                student = Student.objects.filter(user=self.request.user).first()

            if student:
                return FeeInvoice.objects.filter(student=student)

        return FeeInvoice.objects.none()
