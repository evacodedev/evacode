from django.contrib import admin

from .models import GoodsModel, GroupOfGoods


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
