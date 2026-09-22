import re

from rest_framework import serializers

from .models import CONTENT_LANGUAGES, GoodsModel, ImageModel, GroupOfGoods
from .product_content import strip_html
from .product_content_agent import _normalize_section_blocks

CONTENT_LANG_CODES = tuple(code for code, _ in CONTENT_LANGUAGES)
CARD_EXCERPT_LEN = 180


def _card_excerpt(description):
    plain = re.sub(r"\s+", " ", strip_html(description or "")).strip()
    if len(plain) <= CARD_EXCERPT_LEN:
        return plain
    return plain[:CARD_EXCERPT_LEN].rsplit(" ", 1)[0]


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
    payload = {"slug": obj.slug, "name": name}
    if hasattr(obj, "page_published"):
        payload["page"] = bool(obj.page_published)
    return payload


def serialize_brand_page(brand, lang):
    translation = _pick_i18n(list(brand.translations.all()), lang)
    facts = list(translation.facts) if translation and translation.facts else []
    lines = list(translation.lines) if translation and translation.lines else []
    return {
        "slug": brand.slug,
        "name": (translation.name if translation else "") or brand.slug,
        "native_caption": brand.native_caption or "",
        "official_url": brand.official_url or "",
        "logo": brand.logo or "",
        "hero": brand.hero or "",
        "history_image": brand.history_image or "",
        "video_url": brand.video_url or "",
        "lead": (translation.lead if translation else "") or "",
        "history_title": (translation.history_title if translation else "") or "",
        "history": (translation.history if translation else "") or "",
        "mission_title": (translation.mission_title if translation else "") or "",
        "mission": (translation.mission if translation else "") or "",
        "partnership_title": (translation.partnership_title if translation else "") or "",
        "partnership": (translation.partnership if translation else "") or "",
        "facts": facts,
        "lines": lines,
        "gallery": list(translation.gallery) if translation and translation.gallery else [],
        "video_title": (translation.video_title if translation else "") or "",
    }


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
        return _normalize_section_blocks(blocks)


class GoodsListSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()

    class Meta:
        model = GoodsModel
        fields = (
            'id',
            'title',
            'excerpt',
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

    def get_excerpt(self, obj):
        return _card_excerpt(obj.description)


class GroupOfGoodsSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)

    class Meta:
        model = GroupOfGoods
        fields = ('id', 'default_order', 'site_order', 'deleted', 'isaction', 'description', 'name', 'parent_id', 'updated', 'images')
