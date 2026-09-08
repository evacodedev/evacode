from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .business_ru_orders import export_paid_order
from .ems_tariffs import import_ems_xlsx
from .models import (
    EmsDestination,
    EmsRate,
    EmsRateColumn,
    GoodsModel,
    GroupOfGoods,
    PartnerApiKey,
    SiteOrder,
    SiteOrderItem,
)


@admin.register(PartnerApiKey)
class PartnerApiKeyAdmin(admin.ModelAdmin):
    list_display = ("name", "token", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "token")
    readonly_fields = ("created_at",)


@admin.register(GroupOfGoods)
class GroupOfGoodsAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "isaction", "site_order", "deleted", "default_order")
    list_editable = ("isaction", "site_order")
    list_filter = ("isaction", "deleted")
    search_fields = ("name",)


@admin.register(GoodsModel)
class GoodsModelAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "stock", "queue", "weight", "retail_price")
    list_editable = ("queue",)
    search_fields = ("title", "id")
    list_per_page = 50


@admin.register(EmsRateColumn)
class EmsRateColumnAdmin(admin.ModelAdmin):
    list_display = ("title", "code", "sort", "updated_at")
    search_fields = ("code", "title")


@admin.register(EmsRate)
class EmsRateAdmin(admin.ModelAdmin):
    list_display = ("column", "weight_grams", "price_krw")
    list_filter = ("column",)
    search_fields = ("column__code", "column__title")


@admin.register(EmsDestination)
class EmsDestinationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "rate_column", "has_tariff", "sort", "is_active")
    list_editable = ("sort", "is_active", "rate_column")
    list_filter = ("is_active",)
    search_fields = ("code", "name")
    change_list_template = "admin/market/emsdestination/change_list.html"

    @admin.display(boolean=True, description="Тариф")
    def has_tariff(self, obj):
        return obj.can_calculate

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                "import-xlsx/",
                self.admin_site.admin_view(self.import_xlsx_view),
                name="market_emsdestination_import_xlsx",
            ),
        ]
        return extra + urls

    def import_xlsx_view(self, request):
        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "title": "Загрузка тарифов EMS",
        }
        if request.method == "POST":
            upload = request.FILES.get("xlsx")
            if not upload:
                messages.error(request, "Выберите файл .xlsx")
                return render(request, "admin/market/emsdestination/import_xlsx.html", context)
            try:
                result = import_ems_xlsx(upload)
            except Exception as exc:
                messages.error(request, f"Не удалось прочитать файл: {exc}")
                return render(request, "admin/market/emsdestination/import_xlsx.html", context)
            sample = result.get("sample")
            sample_text = ""
            if sample:
                sample_text = (
                    f" Контроль: {sample['column']} {sample['weight_grams']} г = {sample['price_krw']} ₩."
                )
            messages.success(
                request,
                (
                    f"Загружено колонок: {result['column_count']}, "
                    f"ставок: {result['rate_count']}.{sample_text}"
                ),
            )
            return redirect(reverse("admin:market_emsdestination_changelist"))
        return render(request, "admin/market/emsdestination/import_xlsx.html", context)


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
        "shipping_method",
        "shipping_destination",
        "shipping_krw",
        "goods_krw",
        "weight_grams",
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
