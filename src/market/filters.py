from django.db.models import F, Q
from django_filters import BooleanFilter, CharFilter, FilterSet, NumberFilter
from rest_framework.filters import OrderingFilter

from .models import GoodsModel


class GoodsOrderingFilter(OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view) or ["title"]
        user_order = [field for field in ordering if field.lstrip("-") != "queue"]
        return queryset.order_by(
            F("queue").asc(nulls_last=True),
            *user_order,
            "id",
        )


def _slug_list(value):
    return [part.strip() for part in str(value or "").split(",") if part.strip()]


class GoodsFilter(FilterSet):
    id = CharFilter(lookup_expr="exact", required=False)
    category = CharFilter(field_name="category__id", lookup_expr="exact", required=False)
    brand = CharFilter(method="filter_brand", required=False)
    kind = CharFilter(method="filter_kind", required=False)
    bestseller = BooleanFilter(field_name="bestseller", required=False)
    search = CharFilter(method="filter_search", required=False)
    min_price = NumberFilter(field_name="retail_price", lookup_expr="gte", required=False)
    max_price = NumberFilter(field_name="retail_price", lookup_expr="lte", required=False)

    class Meta:
        model = GoodsModel
        fields = [
            "id",
            "category",
            "brand",
            "kind",
            "bestseller",
            "search",
            "min_price",
            "max_price",
        ]

    def filter_search(self, queryset, name, value):
        query = (value or "").strip()
        if not query:
            return queryset
        return queryset.filter(Q(title__icontains=query) | Q(description__icontains=query))

    def filter_brand(self, queryset, name, value):
        slugs = _slug_list(value)
        if not slugs:
            return queryset
        return queryset.filter(content_brand__slug__in=slugs)

    def filter_kind(self, queryset, name, value):
        slugs = _slug_list(value)
        if not slugs:
            return queryset
        return queryset.filter(content_kind__slug__in=slugs)
