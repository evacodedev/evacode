import asyncio
import json
from pprint import pprint
from datetime import datetime, timedelta
import requests
from asgiref.sync import async_to_sync
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
import os

from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
import logging

from .sitemap import catalog_sitemap_urls
from .yandex_feed import cached_yandex_feed
from .home import build_home_page
from .filters import GoodsFilter, GoodsOrderingFilter
from django_filters import rest_framework as filters
from .pagination import CustomPagination, AllObjectPagination
from .auth import IsPartnerOrStaff, OptionalJWTAuthentication, PartnerApiKeyAuthentication
from .utils import (
    BusinessRuBarcodeLookup,
    BusinessRuGoodPricesLookup,
    BusinessRuService,
    serialize_business_ru_good,
)
from rest_framework import generics, status
from rest_framework.viewsets import ModelViewSet
from .models import CheckoutSettings, GoodsModel, GroupOfGoods, ProductBrand, ProductKind
from .product_content import KIND_KEYWORDS
from .serializers import (
    GoodsListSerializer,
    GoodsSerializer,
    GroupOfGoodsSerializer,
    _named_label,
    content_language_from_request,
    serialize_brand_page,
)
from django.http import HttpResponse, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, F, Q

from .checkout_request import build_consult_text, build_telegram_order_text
from .manager_notify import notify_managers

load_dotenv()

logger = logging.getLogger(__name__)


class GoodsAPIView(ModelViewSet):
    queryset = GoodsModel.objects.filter(stock__gt=0).distinct()
    serializer_class = GoodsSerializer
    pagination_class = CustomPagination
    filter_backends = (filters.DjangoFilterBackend, GoodsOrderingFilter)
    filterset_class = GoodsFilter
    ordering_fields = ["retail_price", "title"]
    ordering = ["title"]

    def get_queryset(self):
        qs = super().get_queryset()
        if getattr(self, "action", None) == "list":
            return qs.select_related("content_brand", "content_kind").prefetch_related(
                "images",
                "content_brand__translations",
                "content_kind__translations",
            )
        return qs.select_related("content_brand", "content_kind", "pdp_content").prefetch_related(
            "images",
            "content_brand__translations",
            "content_kind__translations",
            "pdp_content__blocks__translations",
        )

    def get_serializer_class(self):
        if self.action == "list":
            return GoodsListSerializer
        return GoodsSerializer


class GoodsByBarcodeView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [PartnerApiKeyAuthentication]

    def get(self, request):
        barcode = str(request.query_params.get("barcode") or request.query_params.get("code") or "").strip()
        if not barcode:
            return Response({"detail": "Укажите barcode"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            goods = BusinessRuBarcodeLookup().find_all(barcode)
        except Exception:
            logger.exception("Поиск товара по штрихкоду %s в Business.Ru не удался", barcode)
            return Response(
                {"detail": "Не удалось запросить товар в Business.Ru"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        if not goods:
            return Response({"detail": "Товар не найден"}, status=status.HTTP_404_NOT_FOUND)
        results = [serialize_business_ru_good(good, barcode) for good in goods]
        return Response({"count": len(results), "results": results})


class GoodsKrwPricesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [PartnerApiKeyAuthentication]

    def get(self, request, good_id=None):
        raw_id = good_id if good_id is not None else request.query_params.get("id")
        try:
            wanted = int(str(raw_id or "").strip())
        except (TypeError, ValueError):
            return Response({"detail": "Укажите id товара"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            payload = BusinessRuGoodPricesLookup().get(wanted)
        except Exception:
            logger.exception("Цены товара %s в Business.Ru не удалось получить", wanted)
            return Response(
                {"detail": "Не удалось запросить товар в Business.Ru"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        if not payload:
            return Response({"detail": "Товар не найден"}, status=status.HTTP_404_NOT_FOUND)
        return Response(payload)


KIND_FACET_ORDER = {slug: index for index, (slug, *_rest) in enumerate(KIND_KEYWORDS)}


def _facet_rows(queryset, lang, order_key=None):
    rows = []
    for item in queryset:
        label = _named_label(item, lang) or {"slug": item.slug, "name": item.slug}
        rows.append({"slug": label["slug"], "name": label["name"], "count": item.count})
    if order_key:
        rows.sort(key=order_key)
    return rows


class CatalogSitemapAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"urls": catalog_sitemap_urls()})


class YandexFeedView(View):
    def get(self, request):
        try:
            body = cached_yandex_feed()
        except ValueError:
            logger.exception("Yandex feed: нет курса KRW/RUB")
            return HttpResponse("Feed unavailable", status=503, content_type="text/plain; charset=utf-8")
        return HttpResponse(body, content_type="application/xml; charset=utf-8")


class HomePageAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(build_home_page(request))


class BrandPageAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        lang = content_language_from_request(request)
        brand = (
            ProductBrand.objects.filter(slug=slug, page_published=True)
            .prefetch_related("translations")
            .first()
        )
        if brand is None:
            return Response({"detail": "Страница бренда не найдена"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serialize_brand_page(brand, lang))


class CatalogFacetsAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        lang = content_language_from_request(request)
        in_stock = Q(goods__stock__gt=0)
        brands = ProductBrand.objects.annotate(
            count=Count("goods", filter=in_stock, distinct=True)
        ).filter(count__gt=0).prefetch_related("translations")
        kinds = ProductKind.objects.annotate(
            count=Count("goods", filter=in_stock, distinct=True)
        ).filter(count__gt=0).prefetch_related("translations")
        return Response(
            {
                "brands": _facet_rows(
                    brands,
                    lang,
                    order_key=lambda row: (row["name"] or "").casefold(),
                ),
                "kinds": _facet_rows(
                    kinds,
                    lang,
                    order_key=lambda row: (
                        KIND_FACET_ORDER.get(row["slug"], 999),
                        (row["name"] or "").casefold(),
                    ),
                ),
            }
        )


class GroupListAPIView(generics.ListAPIView):
    queryset = (
        GroupOfGoods.objects.filter(isaction=True)
        .order_by(F("site_order").asc(nulls_last=True), "id")
    )
    serializer_class = GroupOfGoodsSerializer
    pagination_class = AllObjectPagination


CHECKOUT_REQUESTS_FILE = "orders_list.json"
CHECKOUT_DATE_FORMAT = "%d-%m-%Y %H:%M:%S"
CONSULT_REPEAT_WINDOW = timedelta(hours=2)
ORDER_REPEAT_WINDOW = timedelta(minutes=5)


def _load_checkout_requests() -> dict:
    try:
        with open(CHECKOUT_REQUESTS_FILE, "r") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _recently_sent(requests_log: dict, key: str, window: timedelta) -> bool:
    raw = requests_log.get(key)
    if not raw:
        return False
    try:
        sent_at = datetime.strptime(raw, CHECKOUT_DATE_FORMAT)
    except (TypeError, ValueError):
        return False
    return datetime.now() - sent_at < window


def _remember_checkout_request(requests_log: dict, key: str) -> None:
    requests_log[key] = datetime.now().strftime(CHECKOUT_DATE_FORMAT)
    try:
        with open(CHECKOUT_REQUESTS_FILE, "w") as f:
            json.dump(requests_log, f)
    except OSError:
        logger.warning("Не удалось записать %s", CHECKOUT_REQUESTS_FILE)


@method_decorator(csrf_exempt, name='dispatch')
class Checkout(View):
    def post(self, request):
        if request.content_type != 'application/json':
            return JsonResponse({'error': 'Запрос должен содержать данные JSON'}, status=400)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Некорректный формат JSON'}, status=400)
        user = data.get('user') if isinstance(data, dict) else None
        if not isinstance(user, dict):
            return JsonResponse({'error': 'Нет данных покупателя'}, status=400)
        phone = str(user.get('phone') or '').strip()
        if not phone:
            return JsonResponse({'error': 'Укажите телефон'}, status=400)

        consult = bool(data.get('consult'))
        if not consult and not CheckoutSettings.load().telegram_enabled:
            return JsonResponse({'error': 'Заказ в Telegram сейчас выключен'}, status=403)

        requests_log = _load_checkout_requests()
        if consult:
            key = phone
            if _recently_sent(requests_log, key, CONSULT_REPEAT_WINDOW):
                return JsonResponse({'message': 'Please wait!'}, status=200)
            text = build_consult_text(user)
            subject = f"Консультация с сайта — {phone}"
        else:
            key = f"order:{phone}"
            if _recently_sent(requests_log, key, ORDER_REPEAT_WINDOW):
                return JsonResponse(
                    {'error': 'Заказ с этого телефона уже отправлен. Если нужно что-то изменить — напишите консультанту.'},
                    status=429,
                )
            text = build_telegram_order_text(data)
            subject = f"Заказ с сайта (Telegram) — {phone}"

        if not notify_managers(text, subject=subject, reply_to=str(user.get('email') or '')):
            return JsonResponse(
                {'error': 'Не удалось отправить заявку. Напишите нам в WhatsApp или на orders@evacode.co.kr.'},
                status=502,
            )
        _remember_checkout_request(requests_log, key)
        return JsonResponse({'message': 'DONE!'}, status=200)


class UpdateDataView(APIView):
    permission_classes = [IsAdminUser]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request):
        b = BusinessRuService()
        b.group_to_model()
        b.goods_to_model()
        return HttpResponse(content='Data updated!', status=200)


class AllGoodsView(APIView):
    permission_classes = [IsPartnerOrStaff]
    # OptionalJWT goes first: both it and the partner key read "Authorization: Bearer".
    authentication_classes = [OptionalJWTAuthentication, PartnerApiKeyAuthentication, SessionAuthentication]

    def get(self, request):
        mast_point = GoodsSerializer(GoodsModel.objects.filter(stock__gt=0), many=True).data
        return JsonResponse({'result': mast_point}, safe=False)
