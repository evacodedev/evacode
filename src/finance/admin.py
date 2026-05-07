from django.contrib import admin
from finance.models import InvoiceYookassa, InvoiceTossPayments

# Register your models here.

# @admin.register(InvoiceYookassa)
# class InvoiceYookassaModelAdmin(admin.ModelAdmin):
#     list_display = ("status", "amount", "created_at", "updated_at", "is_paid", "manager_name", "payment_link")
#     readonly_fields = ("payment_link", "payment_id")

    
@admin.register(InvoiceTossPayments)
class InvoiceTossPaymentsModelAdmin(admin.ModelAdmin):
    exclude = ("payment_link", "payment_id", "order_id", "confirm_response", "is_paid", "payload")
    list_display = ("status", "amount", "created_at", "updated_at", "is_paid", "manager_name", "payment_link")
    readonly_fields = ("payment_link", "payment_id", "status", "is_paid")
    search_fields = ("description", "manager_name")
