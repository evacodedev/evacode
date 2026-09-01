from django.contrib import admin

from .models import GroupOfGoods


@admin.register(GroupOfGoods)
class GroupOfGoodsAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "isaction", "deleted", "default_order")
    list_editable = ("isaction",)
    list_filter = ("isaction", "deleted")
    search_fields = ("name",)
