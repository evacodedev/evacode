from django.contrib import admin, messages

from .business_ru_orders import export_paid_order
from .models import GroupOfGoods, SiteOrder, SiteOrderItem


@admin.register(GroupOfGoods)
class GroupOfGoodsAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "isaction", "site_order", "deleted", "default_order")
    list_editable = ("isaction", "site_order")
    list_filter = ("isaction", "deleted")
    search_fields = ("name",)


class SiteOrderItemInline(admin.TabularInline):
    model = SiteOrderItem
    extra = 0
    readonly_fields = ("good", "good_id_snapshot", "title", "quantity", "price_krw", "line_total_krw")


@admin.register(SiteOrder)
class SiteOrderAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "status",
        "first_name",
        "email",
        "phone",
        "amount_krw",
        "amount_usd",
        "paypal_order_id",
        "business_ru_order_number",
        "business_ru_payment_number",
        "business_ru_reservation_number",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = (
        "public_id",
        "email",
        "phone",
        "first_name",
        "paypal_order_id",
        "business_ru_order_number",
        "business_ru_payment_number",
        "business_ru_reservation_number",
    )
    fields = (
        "public_id",
        "status",
        "first_name",
        "phone",
        "email",
        "country",
        "city",
        "address",
        "postal_code",
        "comment",
        "amount_krw",
        "amount_usd",
        "usd_rate_snapshot",
        "paypal_order_id",
        "paypal_capture_id",
        "paypal_receipt_url",
        "business_ru_order_number",
        "business_ru_payment_number",
        "business_ru_reservation_number",
        "business_ru_error",
        "created_at",
        "updated_at",
        "paid_at",
    )
    readonly_fields = fields
    inlines = [SiteOrderItemInline]
    actions = ["export_to_business_ru"]

    @admin.action(description="Выгрузить в Business.Ru")
    def export_to_business_ru(self, request, queryset):
        for order in queryset:
            if order.status != SiteOrder.Status.PAID:
                self.message_user(
                    request,
                    f"{order.public_id}: выгружать можно только оплаченный заказ",
                    level=messages.WARNING,
                )
                continue
            try:
                export_paid_order(order)
                order.refresh_from_db()
                self.message_user(
                    request,
                    f"{order.public_id}: заказ № {order.business_ru_order_number or order.business_ru_order_id}",
                    level=messages.SUCCESS,
                )
            except Exception as exc:
                self.message_user(request, f"{order.public_id}: {exc}", level=messages.ERROR)
