from django.db.models import F, Q
from django_filters import CharFilter, FilterSet, NumberFilter
from rest_framework.filters import OrderingFilter

from .models import GoodsModel


class GoodsOrderingFilter(OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view) or ["title"]
        order_by = [field for field in ordering if field.lstrip("-") != "queue"]
        order_by.append(F("queue").asc(nulls_last=True))
        order_by.append("id")
        return queryset.order_by(*order_by)


class GoodsFilter(FilterSet):
    id = CharFilter(lookup_expr="exact", required=False)
    category = CharFilter(field_name="category__id", lookup_expr="exact", required=False)
    search = CharFilter(method="filter_search", required=False)
    min_price = NumberFilter(field_name="retail_price", lookup_expr="gte", required=False)
    max_price = NumberFilter(field_name="retail_price", lookup_expr="lte", required=False)

    class Meta:
        model = GoodsModel
        fields = ["id", "category", "search", "min_price", "max_price"]

    def filter_search(self, queryset, name, value):
        query = (value or "").strip()
        if not query:
            return queryset
        return queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))
