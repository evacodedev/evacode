from rest_framework import serializers
from .models import GoodsModel, ImageModel, GroupOfGoods


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = ('id', 'sort', 'url')


class GoodsSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = GoodsModel
        fields = ('id', 'title', 'description', 'category', 'type', 'official_price', 'retail_price', 'wholesale_price',
                  'large_wholesale_price', 'stock', 'images', 'bestseller')


class GroupOfGoodsSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = GroupOfGoods
        fields = ('id', 'default_order', 'deleted', 'isaction', 'description', 'name', 'parent_id', 'updated', 'images')
