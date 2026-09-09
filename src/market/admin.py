from django.contrib import admin, messages
from django.db.utils import OperationalError, ProgrammingError
from django.shortcuts import redirect, render
from django.urls import path, reverse

from .br_stock_inventory import BrStockInventoryError, create_stock_inventory
from .business_ru_orders import export_paid_order
from .ems_tariffs import import_ems_xlsx
from .models import (
    ApiKzSync,
    EmsDestination,
    EmsRate,
    EmsRateColumn,
    GoodsModel,
    GroupOfGoods,
    PartnerApiKey,
    SiteOrder,
    SiteOrderItem,
    CheckoutSettings,
)


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


def _held_suffix(summary: dict, id_key: str, held_key: str) -> str:
    if not summary.get(id_key):
        return ""
    if summary.get(held_key):
        return " (проведено)"
    return " (не проведено)"


def _sync_result_text(summary: dict) -> str:
    skipped = summary.get("skipped_unknown_ids") or []
    skipped_posting = summary.get("skipped_posting_ids") or []
    skipped_charge = summary.get("skipped_charge_ids") or []
    text = (
        f"склад {summary.get('store_id')}: остатки {summary.get('current_lines')}, "
        f"API {summary.get('api_lines')}, строк описи {summary.get('inventory_lines')}, "
        f"излишки {summary.get('surplus')}, недостачи {summary.get('shortage')}, "
        f"инвентаризация id={summary.get('inventory_id')}"
    )
    if summary.get("inventory_number"):
        text += f" № {summary['inventory_number']}"
    text += _held_suffix(summary, "inventory_id", "inventory_held")
    if summary.get("posting_id"):
        text += f", оприходование id={summary['posting_id']}"
        if summary.get("posting_number"):
            text += f" № {summary['posting_number']}"
        text += _held_suffix(summary, "posting_id", "posting_held")
    else:
        text += ", оприходование не создано (нет излишков)"
    if summary.get("charge_id"):
        text += f", списание id={summary['charge_id']}"
        if summary.get("charge_number"):
            text += f" № {summary['charge_number']}"
        text += _held_suffix(summary, "charge_id", "charge_held")
    else:
        text += ", списание не создано (нет недостач)"
    if skipped:
        text += f", пропущены в описи id {skipped[:20]}"
    if skipped_posting:
        text += f", пропущены в оприходовании id {skipped_posting[:20]}"
    if skipped_charge:
        text += f", пропущены в списании id {skipped_charge[:20]}"
    text += (
        f", цены: обновлено {summary.get('prices_updated') or 0}"
        f", без изменений {summary.get('prices_unchanged') or 0}"
        f", ошибок {summary.get('prices_failed') or 0}"
        f", товаров {summary.get('prices_goods') or 0}"
    )
    if summary.get("prices_list_id"):
        text += f", назначение цен id={summary['prices_list_id']}"
        if summary.get("prices_list_number"):
            text += f" № {summary['prices_list_number']}"
    skipped_prices = summary.get("skipped_price_ids") or []
    if skipped_prices:
        text += f", цены пропущены {skipped_prices[:20]}"
    held_errors = summary.get("held_errors") or []
    if held_errors:
        text += f", проводка не удалась: {held_errors[:5]}"
    return text


def _create_sync_log(summary: dict | None, *, ok: bool, message: str) -> ApiKzSync:
    summary = summary or {}
    warehouse = str(summary.get("warehouse_code") or "KZ").upper()
    if warehouse not in {ApiKzSync.WAREHOUSE_KZ, ApiKzSync.WAREHOUSE_RU, ApiKzSync.WAREHOUSE_UZ}:
        warehouse = ApiKzSync.WAREHOUSE_KZ
    return ApiKzSync.objects.create(
        warehouse_code=warehouse,
        store_id=str(summary.get("store_id") or "")[:32],
        ok=ok,
        message=message[:4000],
        inventory_id=str(summary.get("inventory_id") or "")[:32],
        inventory_number=str(summary.get("inventory_number") or "")[:32],
        posting_id=str(summary.get("posting_id") or "")[:32],
        posting_number=str(summary.get("posting_number") or "")[:32],
        charge_id=str(summary.get("charge_id") or "")[:32],
        charge_number=str(summary.get("charge_number") or "")[:32],
        prices_updated=int(summary.get("prices_updated") or 0),
        prices_unchanged=int(summary.get("prices_unchanged") or 0),
        prices_failed=int(summary.get("prices_failed") or 0),
        prices_goods=int(summary.get("prices_goods") or 0),
        prices_list_id=str(summary.get("prices_list_id") or "")[:32],
        prices_list_number=str(summary.get("prices_list_number") or "")[:32],
    )


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
        summary = None
        try:
            summary = create_stock_inventory()
            if not summary.get("inventory_id"):
                raise BrStockInventoryError(
                    "Документ инвентаризации не создан: "
                    f"остатки {summary.get('current_lines')}, "
                    f"API {summary.get('api_lines')}, "
                    f"строк описи {summary.get('inventory_lines')}"
                )
        except BrStockInventoryError as extra:
            _create_sync_log(summary, ok=False, message=str(extra))
            messages.error(request, str(extra))
            return redirect(list_url)
        except Exception as extra:
            _create_sync_log(summary, ok=False, message=str(extra))
            messages.error(request, f"Синхронизация не удалась: {extra}")
            return redirect(list_url)

        text = _sync_result_text(summary)
        log = _create_sync_log(summary, ok=True, message=text)
        messages.success(request, text)
        return redirect(reverse("admin:market_apikzsync_change", args=[log.pk]))


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
_API_KZ_MODELS = {"apikzsync"}

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
