from datetime import time as dt_time

from django import forms
from django.contrib import admin, messages
from django.db.utils import OperationalError, ProgrammingError
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils import timezone

from .br_stock_inventory import execute_kz_stock_sync
from .business_ru_orders import export_paid_order
from .ems_tariffs import import_ems_xlsx
from .models import (
    ApiKzSync,
    ApiKzSyncSettings,
    EmsDestination,
    EmsRate,
    EmsRateColumn,
    GoodsModel,
    GroupOfGoods,
    PartnerApiKey,
    ProductBrand,
    ProductBrandI18n,
    ProductContent,
    ProductContentBlock,
    ProductContentBlockI18n,
    ProductKind,
    ProductKindI18n,
    SiteOrder,
    SiteOrderItem,
    CheckoutSettings,
)
from .product_content import apply_product_content


@admin.register(CheckoutSettings)
class CheckoutSettingsAdmin(admin.ModelAdmin):
    list_display = ("paypal_enabled", "telegram_enabled")
    fields = ("paypal_enabled", "telegram_enabled")

    def has_add_permission(self, request):
        try:
            return not CheckoutSettings.objects.exists()
        except (ProgrammingError, OperationalError):
            return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PartnerApiKey)
class PartnerApiKeyAdmin(admin.ModelAdmin):
    list_display = ("name", "token", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "token")
    readonly_fields = ("created_at",)


class ApiKzSyncSettingsForm(forms.ModelForm):
    weekdays = forms.MultipleChoiceField(
        choices=ApiKzSyncSettings.WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Дни недели",
        help_text="Можно выбрать несколько дней. Время одно на все выбранные дни.",
    )

    class Meta:
        model = ApiKzSyncSettings
        fields = ("enabled", "weekdays", "run_time")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raw = ""
        if self.instance and self.instance.pk:
            raw = self.instance.weekdays or ""
        elif "weekdays" in self.initial:
            raw = self.initial.get("weekdays") or ""
        if isinstance(raw, str):
            self.initial["weekdays"] = [item for item in raw.split(",") if item != ""]
        self.fields["run_time"].initial = self.fields["run_time"].initial or dt_time(3, 0)

    def clean_weekdays(self):
        days = self.cleaned_data.get("weekdays") or []
        return ",".join(str(day) for day in days)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("enabled") and not cleaned.get("weekdays"):
            self.add_error("weekdays", "Выберите хотя бы один день недели.")
        return cleaned


@admin.register(ApiKzSyncSettings)
class ApiKzSyncSettingsAdmin(admin.ModelAdmin):
    form = ApiKzSyncSettingsForm
    change_form_template = "admin/market/apikzsyncsettings/change_form.html"
    list_display = ("enabled", "weekdays", "run_time")
    fields = ("enabled", "weekdays", "run_time")

    def has_add_permission(self, request):
        try:
            return not ApiKzSyncSettings.objects.exists()
        except (ProgrammingError, OperationalError):
            return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = ApiKzSyncSettings.load()
        return redirect(reverse("admin:market_apikzsyncsettings_change", args=[obj.pk]))

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        now = timezone.localtime()
        context["server_tz"] = timezone.get_current_timezone_name()
        context["server_time_display"] = now.strftime("%Y-%m-%d %H:%M:%S")
        context["server_time_iso"] = now.isoformat()
        return super().render_change_form(request, context, add, change, form_url, obj)


@admin.register(ApiKzSync)
class ApiKzSyncAdmin(admin.ModelAdmin):
    change_list_template = "admin/market/apikzsync/change_list.html"
    list_display = (
        "run_at",
        "warehouse_code",
        "store_id",
        "ok",
        "inventory_number",
        "posting_number",
        "charge_number",
        "prices_updated",
        "prices_unchanged",
        "prices_failed",
    )
    list_filter = ("warehouse_code", "ok")
    search_fields = (
        "store_id",
        "inventory_id",
        "inventory_number",
        "posting_id",
        "posting_number",
        "charge_id",
        "charge_number",
        "prices_list_id",
        "prices_list_number",
        "message",
    )
    fields = (
        "run_at",
        "warehouse_code",
        "store_id",
        "ok",
        "inventory_id",
        "inventory_number",
        "posting_id",
        "posting_number",
        "charge_id",
        "charge_number",
        "prices_updated",
        "prices_unchanged",
        "prices_failed",
        "prices_goods",
        "prices_list_id",
        "prices_list_number",
        "message",
    )
    readonly_fields = fields
    ordering = ("-run_at", "-id")

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                "sync/",
                self.admin_site.admin_view(self.sync_view),
                name="market_apikzsync_sync",
            ),
        ]
        return extra + urls

    def sync_view(self, request):
        list_url = reverse("admin:market_apikzsync_changelist")
        if request.method != "POST":
            return redirect(list_url)
        result = execute_kz_stock_sync()
        if result.get("busy"):
            messages.warning(request, result["message"])
            return redirect(list_url)
        if result.get("ok") and result.get("log") is not None:
            messages.success(request, result["message"])
            return redirect(reverse("admin:market_apikzsync_change", args=[result["log"].pk]))
        messages.error(request, result["message"])
        return redirect(list_url)


@admin.register(GroupOfGoods)
class GroupOfGoodsAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "isaction", "site_order", "deleted", "default_order")
    list_editable = ("isaction", "site_order")
    list_filter = ("isaction", "deleted")
    search_fields = ("name",)


class ProductBrandI18nInline(admin.TabularInline):
    model = ProductBrandI18n
    extra = 1


@admin.register(ProductBrand)
class ProductBrandAdmin(admin.ModelAdmin):
    list_display = ("slug",)
    search_fields = ("slug", "translations__name")
    inlines = (ProductBrandI18nInline,)


class ProductKindI18nInline(admin.TabularInline):
    model = ProductKindI18n
    extra = 1


@admin.register(ProductKind)
class ProductKindAdmin(admin.ModelAdmin):
    list_display = ("slug",)
    search_fields = ("slug", "translations__name")
    inlines = (ProductKindI18nInline,)


class ProductContentBlockI18nInline(admin.TabularInline):
    model = ProductContentBlockI18n
    extra = 0


@admin.register(ProductContentBlock)
class ProductContentBlockAdmin(admin.ModelAdmin):
    list_display = ("id", "content", "kind", "sort")
    list_filter = ("kind",)
    search_fields = ("content__good__title",)
    inlines = (ProductContentBlockI18nInline,)


class ProductContentBlockInline(admin.TabularInline):
    model = ProductContentBlock
    extra = 0
    show_change_link = True


@admin.register(ProductContent)
class ProductContentAdmin(admin.ModelAdmin):
    list_display = ("good", "enrichment_status", "parsed_at")
    list_filter = ("enrichment_status",)
    search_fields = ("good__title", "good_id")
    readonly_fields = ("enrichment_status", "enrichment_reasons", "parsed_at")
    inlines = (ProductContentBlockInline,)


@admin.register(GoodsModel)
class GoodsModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "content_brand",
        "content_kind",
        "enrichment_label",
        "stock",
        "queue",
        "weight",
        "retail_price",
    )
    list_editable = ("queue",)
    list_filter = ("content_brand", "content_kind", "pdp_content__enrichment_status")
    search_fields = ("title", "id")
    list_per_page = 50
    autocomplete_fields = ("content_brand", "content_kind")
    actions = ("parse_product_content_action",)
    change_form_template = "admin/market/goodsmodel/change_form.html"
    readonly_fields = ("has_pdp_content", "enrichment_label")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("pdp_content")

    @admin.display(boolean=True, description="Контент")
    def has_pdp_content(self, obj):
        return hasattr(obj, "pdp_content")

    @admin.display(description="Описание BR")
    def enrichment_label(self, obj):
        try:
            content = obj.pdp_content
        except ProductContent.DoesNotExist:
            return "нет"
        if content.enrichment_status == "ok":
            return "достаточно"
        reasons = ", ".join(content.enrichment_reasons or [])
        return f"нужно обогащение ({reasons})" if reasons else "нужно обогащение"

    @admin.action(description="Создать контент и распарсить описание")
    def parse_product_content_action(self, request, queryset):
        parsed = 0
        for good in queryset:
            apply_product_content(good, force=True)
            parsed += 1
        self.message_user(request, f"Разобрано товаров: {parsed}", messages.SUCCESS)

    def get_urls(self):
        urls = super().get_urls()
        extra = [
            path(
                "<path:object_id>/parse-content/",
                self.admin_site.admin_view(self.parse_content_view),
                name="market_goodsmodel_parse_content",
            ),
        ]
        return extra + urls

    def parse_content_view(self, request, object_id):
        if request.method != "POST":
            return redirect(reverse("admin:market_goodsmodel_change", args=[object_id]))
        good = GoodsModel.objects.filter(pk=object_id).first()
        if not good:
            messages.error(request, "Товар не найден")
            return redirect(reverse("admin:market_goodsmodel_changelist"))
        apply_product_content(good, force=True)
        messages.success(request, "Контент создан, описание разобрано")
        return redirect(reverse("admin:market_goodsmodel_change", args=[object_id]))


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
            except Exception as extra:
                messages.error(request, f"Не удалось прочитать файл: {extra}")
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
            except Exception as extra:
                self.message_user(request, f"{order.public_id}: {extra}", level=messages.ERROR)


_EMS_MODELS = {"emsratecolumn", "emsrate", "emsdestination"}
_SETTINGS_MODELS = {"partnerapikey"}
_API_KZ_MODELS = {"apikzsync", "apikzsyncsettings"}

_original_get_app_list = admin.site.get_app_list


def _app_group(name, app_label, models):
    if not models:
        return None
    return {
        "name": name,
        "app_label": app_label,
        "app_url": models[0].get("admin_url"),
        "has_module_perms": True,
        "models": models,
    }


def get_app_list(request, app_label=None):
    app_list = _original_get_app_list(request, app_label)
    ems_models = []
    settings_models = []
    api_kz_models = []
    for app in app_list:
        if app.get("app_label") != "market":
            continue
        remaining = []
        for model in app.get("models") or []:
            object_name = str(model.get("object_name") or "").lower()
            if object_name in _EMS_MODELS:
                ems_models.append(model)
            elif object_name in _SETTINGS_MODELS:
                settings_models.append(model)
            elif object_name in _API_KZ_MODELS:
                api_kz_models.append(model)
            else:
                remaining.append(model)
        app["models"] = remaining

    extras = [
        group
        for group in (
            _app_group("API KZ", "api_kz", api_kz_models),
            _app_group("EMS", "ems", ems_models),
            _app_group("SETTINGS", "settings", settings_models),
        )
        if group
    ]
    if not extras:
        return app_list

    result = []
    inserted = False
    for app in app_list:
        result.append(app)
        if app.get("app_label") == "market":
            result.extend(extras)
            inserted = True
    if not inserted:
        result.extend(extras)

    if app_label in {"ems", "settings", "api_kz"}:
        return [app for app in result if app.get("app_label") == app_label]
    return result


admin.site.get_app_list = get_app_list
