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
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import logging

from .sitemap import catalog_sitemap_urls
from .home import build_home_page
from .filters import GoodsFilter, GoodsOrderingFilter
from django_filters import rest_framework as filters
from .pagination import CustomPagination, AllObjectPagination
from .auth import PartnerApiKeyAuthentication
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
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiohttp import web

load_dotenv()

logger = logging.getLogger(__name__)

token = os.getenv('BOT_TOKEN')
chat_id = os.getenv('CHAT_ID')

bot = Bot(token=token)

keyboard = types.InlineKeyboardMarkup().add(InlineKeyboardButton(text='Обработано✅', callback_data='handle'))


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


@method_decorator(csrf_exempt, name='dispatch')
class Checkout(View):
    def post(self, request):
        if request.content_type == 'application/json':
            try:
                date_format = "%d-%m-%Y %H:%M:%S"
                data = json.loads(request.body)

                with open("orders_list.json", "r") as f:
                    orders_data = json.load(f)

                if data['user']['phone'] in orders_data:
                    last_order_time = datetime.strptime(orders_data[data['user']['phone']], date_format)
                    diff = datetime.now() - last_order_time
                    if diff.seconds / 3600 < 2:
                        print(f"Message not send! {diff.seconds / 3600}")
                        return JsonResponse({'message': 'Please wait!'}, status=200)

                consult = bool(data.get('consult'))
                if not consult and not CheckoutSettings.load().telegram_enabled:
                    return JsonResponse({'error': 'Заказ в Telegram сейчас выключен'}, status=403)

                orders_data[data['user']['phone']] = datetime.now().strftime(date_format)

                message_text = 'ЗАКАЗ С САЙТА:\n'
                if consult:
                    message_text += f"Консультация - {data['user']['phone']}"
                    n = async_to_sync(bot.send_message)(chat_id=chat_id, text=message_text, reply_markup=keyboard)
                else:
                    for good in data['cart']:
                        message_text += f'{good["title"]} - {good["quantity"]}шт - {good["retail_price"]}\n'
                    message_text += f'ФИО: {data["user"]["firstName"]}\n' \
                                    f'Номер: {data["user"]["phone"]}\n' \
                                    f'Индекс: {data["user"].get("postalCode") or ""}\n'

                    n = async_to_sync(bot.send_message)(chat_id=chat_id, text=message_text, reply_markup=keyboard)
                print("Message send!")
                with open('orders_list.json', 'w') as f:
                    json.dump(orders_data, f)

                return JsonResponse({'message': 'DONE!'}, status=200)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Некорректный формат JSON'}, status=400)
        else:
            return JsonResponse({'error': 'Запрос должен содержать данные JSON'}, status=400)


def update_data(request):
    b = BusinessRuService()
    b.group_to_model()
    b.goods_to_model()
    return HttpResponse(content='Data updated!', status=200)


def get_all_goods(request):
    mast_point = GoodsSerializer(GoodsModel.objects.filter(stock__gt=0), many=True).data
    data = {'result': mast_point}
    # out.write(json.dumps(data, ensure_ascii=False))
    return JsonResponse(data, safe=False)
