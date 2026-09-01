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

from .filters import GoodsFilter
from django_filters import rest_framework as filters
from .pagination import CustomPagination, AllObjectPagination
from .utils import BusinessRuService, BusinessRuAPIClient
from rest_framework.filters import OrderingFilter
from rest_framework import generics
from rest_framework.viewsets import ModelViewSet
from .models import GoodsModel, GroupOfGoods
from .serializers import GoodsSerializer, GroupOfGoodsSerializer
from django.http import HttpResponse, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F, IntegerField, Value
from django.db.models.functions import Cast, NullIf
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiohttp import web

load_dotenv()

token = os.getenv('BOT_TOKEN')
chat_id = os.getenv('CHAT_ID')

bot = Bot(token=token)

keyboard = types.InlineKeyboardMarkup().add(InlineKeyboardButton(text='Обработано✅', callback_data='handle'))


class GoodsAPIView(ModelViewSet):
    queryset = GoodsModel.objects.all().distinct()
    serializer_class = GoodsSerializer
    pagination_class = CustomPagination
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = GoodsFilter
    ordering_fields = ["retail_price", "title"]
    ordering = ["retail_price", "title"]


class GroupListAPIView(generics.ListAPIView):
    queryset = (
        GroupOfGoods.objects.filter(isaction=True)
        .annotate(_sort=Cast(NullIf("default_order", Value("")), IntegerField()))
        .order_by(F("_sort").asc(nulls_last=True), "id")
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

                orders_data[data['user']['phone']] = datetime.now().strftime(date_format)

                message_text = 'ЗАКАЗ С САЙТА:\n'
                if data['consult']:
                    message_text += f"Консультация - {data['user']['phone']}"
                    n = async_to_sync(bot.send_message)(chat_id=chat_id, text=message_text, reply_markup=keyboard)
                else:
                    for good in data['cart']:
                        message_text += f'{good["title"]} - {good["quantity"]}шт - {good["retail_price"]}\n'
                    message_text += f'ФИО: {data["user"]["firstName"]}\n' \
                                    f'Номер: {data["user"]["phone"]}\n'

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
    mast_point = GoodsSerializer(GoodsModel.objects.all(), many=True).data
    data = {'result': mast_point}
    # out.write(json.dumps(data, ensure_ascii=False))
    return JsonResponse(data, safe=False)
