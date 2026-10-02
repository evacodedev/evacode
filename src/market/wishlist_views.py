from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GoodsModel, WishlistItem
from .serializers import GoodsListSerializer


def _card_queryset():
    return GoodsModel.objects.select_related("content_brand", "content_kind").prefetch_related(
        "images",
        "content_brand__translations",
        "content_kind__translations",
    )


def _saved_goods(user):
    return (
        _card_queryset()
        .filter(wishlist_items__user=user)
        .order_by("-wishlist_items__created_at", "-wishlist_items__id")
    )


def _goods_id(request):
    raw = request.data.get("goods_id")
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        goods = _saved_goods(request.user)
        data = GoodsListSerializer(goods, many=True, context={"request": request}).data
        return Response(data)

    def post(self, request):
        goods_id = _goods_id(request)
        if goods_id is None:
            return Response({"detail": "Укажите товар"}, status=status.HTTP_400_BAD_REQUEST)
        goods = _card_queryset().filter(pk=goods_id).first()
        if goods is None:
            return Response({"detail": "Товар не найден"}, status=status.HTTP_404_NOT_FOUND)
        _, created = WishlistItem.objects.get_or_create(user=request.user, goods=goods)
        payload = GoodsListSerializer(goods, context={"request": request}).data
        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(payload, status=code)


class WishlistItemView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, goods_id):
        deleted, _ = WishlistItem.objects.filter(user=request.user, goods_id=goods_id).delete()
        if not deleted:
            return Response({"detail": "Нет в избранном"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
