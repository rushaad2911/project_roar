from django.urls import path
from . import views

urlpatterns = [
    # Fee Category URLs
    path('categories/', views.FeeCategoryListView.as_view(), name='fee_category_list'),
    path('categories/create/', views.FeeCategoryCreateView.as_view(), name='fee_category_create'),
    path('categories/<int:pk>/update/', views.FeeCategoryUpdateView.as_view(), name='fee_category_update'),
    path('categories/<int:pk>/delete/', views.FeeCategoryDeleteView.as_view(), name='fee_category_delete'),
    
    # Fee Invoice URLs
    path('invoices/', views.FeeInvoiceListView.as_view(), name='fee_invoice_list'),
    path('invoices/<int:pk>/', views.FeeInvoiceDetailView.as_view(), name='fee_invoice_detail'),
    path('invoices/create/', views.FeeInvoiceCreateView.as_view(), name='fee_invoice_create'),
    path('invoices/<int:pk>/update/', views.FeeInvoiceUpdateView.as_view(), name='fee_invoice_update'),
    path('invoices/<int:pk>/delete/', views.FeeInvoiceDeleteView.as_view(), name='fee_invoice_delete'),
    
    # Payment URLs
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment_create'),
    path('invoices/<int:invoice_id>/payment/', views.create_payment_for_invoice, name='create_payment_for_invoice'),
    
    # Student Fee URLs
    path('my-fees/', views.StudentFeeListView.as_view(), name='student_fee_list'),
]
