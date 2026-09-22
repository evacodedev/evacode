from django.db.models import Q

from market.models import GoodsModel, ProductBrand, ProductBrandI18n

JOGABI_IMG = "/images/brands/jogabi"

JOGABI_PAGE = {
    "slug": "jogabi",
    "page_published": True,
    "official_url": "https://ewhajogabi.com/",
    "video_url": "https://www.youtube.com/watch?v=kT6It0g0jgA",
    "native_caption": "이화조개비",
    "logo": f"{JOGABI_IMG}/logo.jpg",
    "hero": f"{JOGABI_IMG}/hero.jpg",
    "history_image": f"{JOGABI_IMG}/history.jpg",
    "name": "JOGABI",
    "lead": (
        "Оригинальный уход Ewha Dermatology с 1943 года. "
        "Медицинская косметика, чьё имя родилось из ракушки."
    ),
    "history_title": "Имя из ракушки",
    "history": (
        "В 1943 году в Сеуле появилась Ewha Jogabi — для тех, кто страдал от кожных заболеваний. "
        "Тары почти не было: мазь разливали в ракушки, собранные в тот же день. "
        "Средство оказалось настолько действенным, что о нём узнала вся страна. "
        "Так jogabi — «ракушка» — стало именем ухода.\n\n"
        "Больше восьмидесяти лет Ewha Dermatology лечила кожу и копила клинический опыт. "
        "На этом опыте собрана линейка JOGABI: не воспоминание о мази, а современный медицинский уход, "
        "выверенный специалистами."
    ),
    "mission_title": "Наследие и наука",
    "mission": (
        "JOGABI соединяет дерматологическое наследие Ewha с современной биотехнологией. "
        "Формулы рассчитаны на разные задачи кожи — спокойный ежедневный уход, антиоксидантную поддержку, "
        "работу с несовершенствами — и держат обещание клиники: точность и доверие, а не эффект сезона."
    ),
    "facts": [
        {"value": "1943", "label": "История бренда начинается в Сеуле."},
    ],
    "lines": [
        {
            "title": "The Originals",
            "body": (
                "Сигнатурная линия, которая восемьдесят лет жила внутри Ewha Dermatology. "
                "Формулы из рецептурных мазей аптеки и клиники Ewha, обновлённые современной биотехнологией: "
                "кремы под разные состояния кожи."
            ),
            "image": f"{JOGABI_IMG}/originals.jpg",
        },
        {
            "title": "The Professionals",
            "body": (
                "Профессиональный антиоксидантный уход. Восемьдесят лет наблюдений за кожей "
                "и современная наука — в линиях Refine Cell Boost."
            ),
            "image": f"{JOGABI_IMG}/professionals.jpg",
        },
        {
            "title": "The Acne",
            "body": (
                "Уход для проблемной кожи: акне, жирность, раздражение. "
                "Клинический опыт Ewha Dermatology — в том числе тысячи приёмов по акне — "
                "собран в линейке AC Control."
            ),
            "image": f"{JOGABI_IMG}/acne.jpg",
        },
    ],
    "partnership_title": "Эксклюзив для России и СНГ",
    "partnership": (
        "11 сентября 2026 года в Корее EvaCode и JOGABI подписали соглашение об эксклюзивной дистрибуции. "
        "EvaCode — официальный партнёр бренда на рынках России и СНГ: прямая поставка, оригинальный уход "
        "и общая ответственность за то, как JOGABI появляется у клиента."
    ),
    "gallery": [
        {
            "image": f"{JOGABI_IMG}/exclusive-signing.jpg",
            "alt": "Подписание эксклюзивного соглашения EvaCode и JOGABI, 11 сентября 2026",
        },
        {
            "image": f"{JOGABI_IMG}/exclusive-ceremony.jpg",
            "alt": "Церемония подписания эксклюзивного соглашения JOGABI и EvaCode",
        },
        {
            "image": f"{JOGABI_IMG}/exclusive-meeting.jpg",
            "alt": "Встреча EvaCode и JOGABI в Dermalcode Skin Care Academy",
        },
    ],
    "video_title": "Фильм JOGABI",
}

JOGABI_TITLE_Q = (
    Q(title__icontains="jogabi")
    | Q(title__icontains="jagobi")
    | Q(title__icontains="조가비")
)


def ensure_jogabi_brand(*, link_goods: bool = True) -> ProductBrand:
    data = JOGABI_PAGE
    brand, _created = ProductBrand.objects.get_or_create(slug=data["slug"])
    brand.page_published = data["page_published"]
    brand.official_url = data["official_url"]
    brand.native_caption = data["native_caption"]
    brand.logo = data["logo"]
    brand.hero = data["hero"]
    brand.history_image = data["history_image"]
    brand.video_url = data.get("video_url") or ""
    brand.save()
    ProductBrandI18n.objects.update_or_create(
        brand=brand,
        language="ru",
        defaults={
            "name": data["name"],
            "lead": data["lead"],
            "history_title": data["history_title"],
            "history": data["history"],
            "mission_title": data["mission_title"],
            "mission": data["mission"],
            "facts": data["facts"],
            "lines": data["lines"],
            "partnership_title": data["partnership_title"],
            "partnership": data["partnership"],
            "gallery": data["gallery"],
            "video_title": data.get("video_title") or "",
        },
    )
    if link_goods:
        GoodsModel.objects.filter(JOGABI_TITLE_Q).update(content_brand=brand)
    return brand
