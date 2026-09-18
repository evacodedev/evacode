import re
from datetime import datetime, time as dt_time, timedelta
from decimal import Decimal

from django.contrib import admin
from django.db.models import Q, Sum
from django.db.utils import OperationalError, ProgrammingError
from django.urls import reverse
from django.utils import timezone

from .models import (
    ApiKzSync,
    GoodsModel,
    ProductContent,
    ProductContentAgentSettings,
    SiteOrder,
)

PREVIEW_LIMIT = 5

_KZ_MESSAGE_FIELDS = (
    ("Остатки", r"остатки (\d+)"),
    ("API", r"API (\d+)"),
    ("Строк описи", r"строк описи (\d+)"),
    ("Излишки", r"излишки (\d+)"),
    ("Недостачи", r"недостачи (\d+)"),
)


def _doc_value(record_id, number, held_note=""):
    if not record_id and not number:
        return "—"
    parts = []
    if record_id:
        parts.append(f"id {record_id}")
    if number:
        parts.append(f"№ {number}")
    text = " · ".join(parts)
    return f"{text}{held_note}" if held_note else text


def kz_sync_rows(last: ApiKzSync):
    when = timezone.localtime(last.run_at).strftime("%Y-%m-%d %H:%M") if last.run_at else "—"
    rows = [
        {"label": "Время", "value": when},
        {"label": "Статус", "value": "успешно" if last.ok else "ошибка"},
        {"label": "Склад BR", "value": last.store_id or "—"},
    ]
    message = last.message or ""
    for label, pattern in _KZ_MESSAGE_FIELDS:
        match = re.search(pattern, message)
        if match:
            rows.append({"label": label, "value": match.group(1)})
    held = " (проведено)" if "(проведено)" in message else ""
    not_held = " (не проведено)" if "(не проведено)" in message else ""
    inv_note = held or not_held
    rows.append(
        {
            "label": "Инвентаризация",
            "value": _doc_value(last.inventory_id, last.inventory_number, inv_note),
        }
    )
    rows.append(
        {
            "label": "Оприходование",
            "value": _doc_value(last.posting_id, last.posting_number) if last.posting_id else "не создано",
        }
    )
    rows.append(
        {
            "label": "Списание",
            "value": _doc_value(last.charge_id, last.charge_number) if last.charge_id else "не создано",
        }
    )
    rows.append(
        {
            "label": "Цены",
            "value": (
                f"обновлено {last.prices_updated}, без изменений {last.prices_unchanged}, "
                f"ошибок {last.prices_failed}, товаров {last.prices_goods}"
            ),
        }
    )
    if last.prices_list_id or last.prices_list_number:
        rows.append(
            {
                "label": "Назначение цен",
                "value": _doc_value(last.prices_list_id, last.prices_list_number),
            }
        )
    return rows


class BrandFilledFilter(admin.SimpleListFilter):
    title = "Бренд заполнен"
    parameter_name = "brand_filled"

    def lookups(self, request, model_admin):
        return (("no", "Без бренда"), ("yes", "С брендом"))

    def queryset(self, request, queryset):
        if self.value() == "no":
            return queryset.filter(content_brand__isnull=True)
        if self.value() == "yes":
            return queryset.filter(content_brand__isnull=False)
        return queryset


class PdpPresenceFilter(admin.SimpleListFilter):
    title = "Контент карточки"
    parameter_name = "pdp"

    def lookups(self, request, model_admin):
        return (("missing", "Нет контента"),)

    def queryset(self, request, queryset):
        if self.value() == "missing":
            return queryset.filter(pdp_content__isnull=True)
        return queryset


class AgentQueueFilter(admin.SimpleListFilter):
    title = "Агент"
    parameter_name = "agent"

    def lookups(self, request, model_admin):
        return (("draft", "Черновик"), ("error", "Ошибка"))

    def queryset(self, request, queryset):
        if self.value() == "draft":
            return queryset.exclude(Q(agent_draft=None) | Q(agent_draft={}))
        if self.value() == "error":
            return queryset.exclude(agent_error="")
        return queryset


class OrderWhenFilter(admin.SimpleListFilter):
    title = "Когда"
    parameter_name = "when"

    def lookups(self, request, model_admin):
        return (("today", "Сегодня"),)

    def queryset(self, request, queryset):
        if self.value() == "today":
            _, start, end = day_bounds()
            return queryset.filter(created_at__gte=start, created_at__lt=end)
        return queryset


class OrderOpsFilter(admin.SimpleListFilter):
    title = "Операции"
    parameter_name = "ops"

    def lookups(self, request, model_admin):
        return (
            ("br", "Выгрузка BR"),
            ("mail", "Письмо не ушло"),
        )

    def queryset(self, request, queryset):
        paid = queryset.filter(status=SiteOrder.Status.PAID)
        if self.value() == "br":
            return paid.filter(_br_problem_q())
        if self.value() == "mail":
            return paid.filter(confirmation_email_sent_at__isnull=True)
        return queryset


def day_bounds(now=None):
    now = now or timezone.now()
    day = timezone.localtime(now).date()
    start = timezone.make_aware(datetime.combine(day, dt_time.min))
    return day, start, start + timedelta(days=1)


def _br_problem_q():
    missing_export = Q(business_ru_order_id="") & Q(business_ru_order_number="")
    return Q(business_ru_error__gt="") | missing_export


def _safe_reverse(name, args=None):
    try:
        return reverse(name, args=args or ())
    except Exception:
        return ""


def _changelist(name, query=""):
    url = _safe_reverse(name)
    if url and query:
        return f"{url}?{query}"
    return url


def build_admin_dashboard(request):
    empty = {
        "show_orders": False,
        "show_catalog": False,
        "show_kz": False,
        "day": None,
        "alerts": [],
        "orders": {},
        "catalog": {},
        "kz": {},
    }
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return empty
    try:
        return _build_admin_dashboard(user)
    except (ProgrammingError, OperationalError):
        return empty


def _build_admin_dashboard(user):
    day, start, end = day_bounds()
    today = Q(created_at__gte=start, created_at__lt=end)
    show_orders = user.has_perm("market.view_siteorder")
    show_catalog = user.has_perm("market.view_goodsmodel")
    show_content = user.has_perm("market.view_productcontent")
    show_kz = user.has_perm("market.view_apikzsync")
    alerts = []
    orders = {}
    catalog = {}
    kz = {}

    if show_orders:
        created_qs = SiteOrder.objects.filter(today)
        paid_qs = SiteOrder.objects.filter(status=SiteOrder.Status.PAID, paid_at__gte=start, paid_at__lt=end)
        pending = created_qs.filter(status=SiteOrder.Status.PENDING).count()
        failed = created_qs.filter(status=SiteOrder.Status.FAILED).count()
        paid_all = SiteOrder.objects.filter(status=SiteOrder.Status.PAID)
        br_problem = paid_all.filter(_br_problem_q()).count()
        no_mail = paid_all.filter(confirmation_email_sent_at__isnull=True).count()
        totals = paid_qs.aggregate(krw=Sum("amount_krw"), usd=Sum("amount_usd"))
        orders = {
            "created": created_qs.count(),
            "paid": paid_qs.count(),
            "pending": pending,
            "failed": failed,
            "amount_krw": totals["krw"] or 0,
            "amount_usd": totals["usd"] or Decimal("0"),
            "br_problem": br_problem,
            "no_mail": no_mail,
            "recent": [
                {
                    "label": f"{row.public_id} · {row.get_status_display()} · {row.amount_krw}₩",
                    "url": _safe_reverse("admin:market_siteorder_change", [row.pk]),
                }
                for row in created_qs.order_by("-created_at")[:PREVIEW_LIMIT]
            ],
            "url_today": _changelist("admin:market_siteorder_changelist", "when=today"),
            "url_pending": _changelist(
                "admin:market_siteorder_changelist", "when=today&status__exact=pending"
            ),
            "url_failed": _changelist(
                "admin:market_siteorder_changelist", "when=today&status__exact=failed"
            ),
            "url_br": _changelist("admin:market_siteorder_changelist", "ops=br"),
            "url_mail": _changelist("admin:market_siteorder_changelist", "ops=mail"),
        }
        if pending:
            alerts.append(
                {
                    "tone": "warning",
                    "text": f"Сегодня без оплаты: {pending}",
                    "url": orders["url_pending"],
                }
            )
        if failed:
            alerts.append(
                {
                    "tone": "danger",
                    "text": f"Ошибка оплаты сегодня: {failed}",
                    "url": orders["url_failed"],
                }
            )
        if br_problem:
            alerts.append(
                {
                    "tone": "danger",
                    "text": f"Оплаченные без выгрузки в Business.ru: {br_problem}",
                    "url": orders["url_br"],
                }
            )
        if no_mail:
            alerts.append(
                {
                    "tone": "warning",
                    "text": f"Оплаченные без письма клиенту: {no_mail}",
                    "url": orders["url_mail"],
                }
            )

    if show_catalog:
        no_brand_qs = GoodsModel.objects.filter(content_brand__isnull=True)
        no_brand = no_brand_qs.count()
        no_content = GoodsModel.objects.filter(pdp_content__isnull=True).count()
        catalog = {
            "no_brand": no_brand,
            "no_content": no_content,
            "needs_enrichment": 0,
            "drafts": 0,
            "agent_errors": 0,
            "agent_enabled": None,
            "reasons": [],
            "recent_no_brand": [
                {
                    "label": f"{row.id} · {row.title}",
                    "url": _safe_reverse("admin:market_goodsmodel_change", [row.pk]),
                }
                for row in no_brand_qs.order_by("-id")[:PREVIEW_LIMIT]
            ],
            "recent_enrichment": [],
            "url_no_brand": _changelist("admin:market_goodsmodel_changelist", "brand_filled=no"),
            "url_no_content": _changelist("admin:market_goodsmodel_changelist", "pdp=missing"),
            "url_needs": "",
            "url_drafts": "",
            "url_errors": "",
        }
        if no_brand:
            alerts.append(
                {
                    "tone": "warning",
                    "text": (
                        f"Без бренда: {no_brand}. Справочник заполняется вручную, "
                        "большинство SKU без бренда — ожидаемо."
                    ),
                    "url": catalog["url_no_brand"],
                }
            )
        if show_content:
            needs_qs = ProductContent.objects.filter(enrichment_status="needs_enrichment")
            draft_qs = ProductContent.objects.exclude(Q(agent_draft=None) | Q(agent_draft={}))
            error_qs = ProductContent.objects.exclude(agent_error="")
            catalog["needs_enrichment"] = needs_qs.count()
            catalog["drafts"] = draft_qs.count()
            catalog["agent_errors"] = error_qs.count()
            catalog["url_needs"] = _changelist(
                "admin:market_productcontent_changelist",
                "enrichment_status__exact=needs_enrichment",
            )
            catalog["url_drafts"] = _changelist(
                "admin:market_productcontent_changelist", "agent=draft"
            )
            catalog["url_errors"] = _changelist(
                "admin:market_productcontent_changelist", "agent=error"
            )
            catalog["recent_enrichment"] = [
                {
                    "label": f"{row.good_id} · {row.good.title}",
                    "url": _safe_reverse("admin:market_goodsmodel_change", [row.good_id]),
                }
                for row in needs_qs.select_related("good").order_by("-parsed_at")[:PREVIEW_LIMIT]
            ]
            reason_labels = {
                "empty": "пусто",
                "short": "коротко",
                "no_sections": "нет секций",
                "no_ingredients": "нет состава",
            }
            catalog["reasons"] = []
            for code, label in reason_labels.items():
                count = needs_qs.filter(enrichment_reasons__contains=[code]).count()
                if count:
                    catalog["reasons"].append({"code": code, "label": label, "count": count})
            try:
                catalog["agent_enabled"] = ProductContentAgentSettings.load().enabled
            except (ProgrammingError, OperationalError):
                catalog["agent_enabled"] = None
            if catalog["agent_enabled"] is False:
                alerts.append(
                    {
                        "tone": "info",
                        "text": "Агент контента выключен.",
                        "url": _changelist("admin:market_productcontentagentsettings_changelist"),
                    }
                )
            if catalog["needs_enrichment"]:
                alerts.append(
                    {
                        "tone": "warning",
                        "text": f"Нужно обогатить описание: {catalog['needs_enrichment']}",
                        "url": catalog["url_needs"],
                    }
                )
            if catalog["agent_errors"]:
                alerts.append(
                    {
                        "tone": "danger",
                        "text": f"Ошибка агента: {catalog['agent_errors']}",
                        "url": catalog["url_errors"],
                    }
                )
            if catalog["drafts"]:
                alerts.append(
                    {
                        "tone": "info",
                        "text": f"Черновик агента не принят: {catalog['drafts']}",
                        "url": catalog["url_drafts"],
                    }
                )

    if show_kz:
        last = ApiKzSync.objects.filter(warehouse_code=ApiKzSync.WAREHOUSE_KZ).first()
        kz = {
            "last": None,
            "url": _changelist("admin:market_apikzsync_changelist"),
        }
        if last:
            kz["last"] = {
                "ok": last.ok,
                "when": timezone.localtime(last.run_at).strftime("%Y-%m-%d %H:%M") if last.run_at else "—",
                "rows": kz_sync_rows(last),
            }
            if not last.ok:
                alerts.append(
                    {
                        "tone": "danger",
                        "text": f"Последний синк KZ с ошибкой ({kz['last']['when']}).",
                        "url": kz["url"],
                    }
                )

    return {
        "show_orders": show_orders,
        "show_catalog": show_catalog,
        "show_kz": show_kz,
        "day": day.isoformat(),
        "alerts": alerts,
        "orders": orders,
        "catalog": catalog,
        "kz": kz,
    }


def patch_admin_index():
    admin.site.index_template = "admin/market/dashboard_index.html"
    original = admin.site.index

    def index(request, extra_context=None):
        extra = dict(extra_context or {})
        extra["evacode_dashboard"] = build_admin_dashboard(request)
        return original(request, extra)

    admin.site.index = index
