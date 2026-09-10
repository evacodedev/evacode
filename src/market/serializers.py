from rest_framework import serializers
from .models import CONTENT_LANGUAGES, GoodsModel, ImageModel, GroupOfGoods

CONTENT_LANG_CODES = tuple(code for code, _ in CONTENT_LANGUAGES)


def content_language_from_request(request):
    lang = "ru"
    if request is not None:
        lang = str(request.query_params.get("lang") or "ru").lower()
    if lang not in CONTENT_LANG_CODES:
        return "ru"
    return lang


def _pick_i18n(translations, lang):
    by_lang = {item.language: item for item in translations}
    if lang in by_lang:
        return by_lang[lang]
    for code in CONTENT_LANG_CODES:
        if code in by_lang:
            return by_lang[code]
    return next(iter(translations), None)


def _named_label(obj, lang):
    if obj is None:
        return None
    translation = _pick_i18n(list(obj.translations.all()), lang)
    name = (translation.name if translation else "") or obj.slug
    return {"slug": obj.slug, "name": name}


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageModel
        fields = ('id', 'sort', 'url')


class GoodsSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    content_brand = serializers.SerializerMethodField()
    content_kind = serializers.SerializerMethodField()
    content_blocks = serializers.SerializerMethodField()

    class Meta:
        model = GoodsModel
        fields = (
            'id',
            'title',
            'description',
            'category',
            'type',
            'official_price',
            'retail_price',
            'wholesale_price',
            'large_wholesale_price',
            'stock',
            'weight',
            'images',
            'bestseller',
            'content_brand',
            'content_kind',
            'content_blocks',
        )

    def _lang(self):
        return content_language_from_request(self.context.get("request"))

    def get_content_brand(self, obj):
        return _named_label(obj.content_brand, self._lang())

    def get_content_kind(self, obj):
        return _named_label(obj.content_kind, self._lang())

    def get_content_blocks(self, obj):
        try:
            content = obj.pdp_content
        except GoodsModel.pdp_content.RelatedObjectDoesNotExist:
            return []
        lang = self._lang()
        blocks = []
        for block in content.blocks.all():
            translation = _pick_i18n(list(block.translations.all()), lang)
            blocks.append(
                {
                    "kind": block.kind,
                    "heading": translation.heading if translation else "",
                    "body": translation.body if translation else "",
                    "items": list(translation.items) if translation and translation.items else [],
                }
            )
        return blocks


class GoodsListSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = GoodsModel
        fields = (
            'id',
            'title',
            'category',
            'type',
            'official_price',
            'retail_price',
            'stock',
            'weight',
            'images',
            'bestseller',
        )

    def get_images(self, obj):
        image = next(iter(obj.images.all()), None)
        if image is None:
            return []
        return ImageSerializer([image], many=True).data


class GroupOfGoodsSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = GroupOfGoods
        fields = ('id', 'default_order', 'site_order', 'deleted', 'isaction', 'description', 'name', 'parent_id', 'updated', 'images')
