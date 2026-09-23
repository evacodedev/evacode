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


def _upsert_brand_page(data: dict, *, title_q=None, link_goods: bool = True) -> ProductBrand:
    brand, _created = ProductBrand.objects.get_or_create(slug=data["slug"])
    brand.page_published = data["page_published"]
    brand.official_url = data.get("official_url") or ""
    brand.native_caption = data.get("native_caption") or ""
    brand.logo = data.get("logo") or ""
    brand.hero = data.get("hero") or ""
    brand.history_image = data.get("history_image") or ""
    brand.video_url = data.get("video_url") or ""
    brand.save()
    ProductBrandI18n.objects.update_or_create(
        brand=brand,
        language="ru",
        defaults={
            "name": data["name"],
            "lead": data.get("lead") or "",
            "history_title": data.get("history_title") or "",
            "history": data.get("history") or "",
            "mission_title": data.get("mission_title") or "",
            "mission": data.get("mission") or "",
            "facts": data.get("facts") or [],
            "lines": data.get("lines") or [],
            "partnership_title": data.get("partnership_title") or "",
            "partnership": data.get("partnership") or "",
            "gallery": data.get("gallery") or [],
            "video_title": data.get("video_title") or "",
        },
    )
    if link_goods and title_q is not None:
        GoodsModel.objects.filter(title_q).update(content_brand=brand)
    return brand


def ensure_jogabi_brand(*, link_goods: bool = True) -> ProductBrand:
    return _upsert_brand_page(JOGABI_PAGE, title_q=JOGABI_TITLE_Q, link_goods=link_goods)


CURACION_IMG = "/images/brands/curacion"

CURACION_PAGE = {
    "slug": "curacion",
    "page_published": True,
    "official_url": "https://91cosmedi.com/en/curacion/",
    "video_url": "",
    "native_caption": "큐라씨온",
    "logo": f"{CURACION_IMG}/philosophy.jpg",
    "hero": f"{CURACION_IMG}/hero.jpg",
    "history_image": f"{CURACION_IMG}/history.jpg",
    "name": "Curación",
    "lead": (
        "Lacto-уход Nineone Cosmedi с 2017 года. "
        "Формулы с ферментированными молочными кислотами — для баланса, влаги и спокойной кожи."
    ),
    "history_title": "Имя из исцеления",
    "history": (
        "Curación — от испанского «исцеление». Бренд родился у Nineone Cosmedi как премиальный "
        "эстетический уход для клиник и дома: мягкие формулы с высокой плотностью влаги и питания.\n\n"
        "В основе — лакто-комплекс: ферментированные молочные кислоты, гиалуроновая кислота и "
        "экстракты, которые поддерживают барьер и успокаивают кожу после внешних нагрузок."
    ),
    "mission_title": "Lacto Care",
    "mission": (
        "Линия Lacto Care собрана вокруг одного обещания — восстановить баланс кожи без жёсткого "
        "стресса. Очищение, тоник, эссенция, крем и маски работают как короткий ритуал: влага, "
        "питание и спокойствие день за днём."
    ),
    "facts": [
        {"value": "2017", "label": "Nineone Cosmedi запускает Curación."},
    ],
    "lines": [
        {
            "title": "Milk Cleansing",
            "body": "Мягкое очищение на лактобактериях: снимает загрязнения и оставляет кожу увлажнённой.",
            "image": f"{CURACION_IMG}/history.jpg",
        },
        {
            "title": "Calming Toner",
            "body": "Три ферментированные молочные кислоты и центелла — лёгкое успокоение и влага.",
            "image": f"{CURACION_IMG}/hero.jpg",
        },
        {
            "title": "Barrier Essence",
            "body": "Эссенция с двойным действием: питание, влага и поддержка барьера.",
            "image": f"{CURACION_IMG}/essence.jpg",
        },
        {
            "title": "Repair Cream",
            "body": "Крем-контроль восстановления: центелла, гиалуроновая кислота и лакто-комплекс.",
            "image": f"{CURACION_IMG}/cream.jpg",
        },
        {
            "title": "Aquanic Mask",
            "body": "Кремовая маска для чистой основы тона и мягкого обновления пор.",
            "image": f"{CURACION_IMG}/mask.jpg",
        },
    ],
    "partnership_title": "Эксклюзив для России и СНГ",
    "partnership": (
        "EvaCode и Nineone Cosmedi подписали соглашение об эксклюзивной дистрибуции Curación "
        "на рынках России и СНГ: прямая поставка, оригинальный лакто-уход и общая ответственность "
        "за то, как бренд появляется у клиента."
    ),
    "gallery": [
        {
            "image": f"{CURACION_IMG}/signing-1.jpg",
            "alt": "Подписание соглашения EvaCode и Curación",
        },
        {
            "image": f"{CURACION_IMG}/signing-2.jpg",
            "alt": "Эксклюзивное соглашение Curación для России и СНГ",
        },
        {
            "image": f"{CURACION_IMG}/signing-meeting.jpg",
            "alt": "Встреча EvaCode и команды Curación",
        },
    ],
    "video_title": "",
}

CURACION_TITLE_Q = Q(title__icontains="curacion") | Q(title__icontains="curación") | Q(title__icontains="큐라")


def ensure_curacion_brand(*, link_goods: bool = True) -> ProductBrand:
    return _upsert_brand_page(CURACION_PAGE, title_q=CURACION_TITLE_Q, link_goods=link_goods)


TTT_IMG = "/images/brands/tom-tit-tot"
SIGNING_IMG = "/images/brands/curacion"

TOM_TIT_TOT_PAGE = {
    "slug": "tom-tit-tot",
    "page_published": True,
    "official_url": "https://tomtittot.com/",
    "video_url": "",
    "native_caption": "TTT",
    "logo": f"{TTT_IMG}/ceo.jpg",
    "hero": f"{TTT_IMG}/banner-cpnp.jpg",
    "history_image": f"{TTT_IMG}/placenta.jpg",
    "name": "TOM-TIT-TOT",
    "lead": (
        "Премиальный корейский уход с высокой концентрацией активных компонентов. "
        "Стволовые клетки, PDRN, NMN, золото, ниацинамид и растительная плацента — "
        "ради реальных изменений кожи."
    ),
    "history_title": "Имя из сказки",
    "history": (
        "TOM-TIT-TOT вдохновлён английской сказкой Tom Tit Tot: герой появляется в самый "
        "безвыходный момент и доводит до конца то, что одному было не под силу.\n\n"
        "Так и кожа: когда восстановление, упругость и тон уже не отвечают только на "
        "ежедневный уход, нужна формула с достаточной дозой активных веществ — не "
        "красивое имя ингредиента, а его концентрация."
    ),
    "mission_title": "Содержание важнее тренда",
    "mission": (
        "Мы проектируем состав раньше образа: тренды вторичны, результат — первичен. "
        "Продукты TOM-TIT-TOT используют и дома, и в эстетических салонах: важны "
        "стабильность, плотность ухода и ощутимое улучшение состояния кожи."
    ),
    "facts": [
        {"value": "CPNP", "label": "Регистрация в Европейском союзе."},
        {"value": "FDA", "label": "Соответствие стандартам США."},
        {"value": "MHLW", "label": "Сертификация для Японии."},
    ],
    "lines": [
        {
            "title": "Placenta Care",
            "body": "Растительная плацента, витамин C и ниацинамид — сияние и питание в плотной формуле.",
            "image": f"{TTT_IMG}/placenta.jpg",
        },
        {
            "title": "V15 Ampoule",
            "body": "Курсовые ампулы с высокой долей активов для яркости и ровного тона.",
            "image": f"{TTT_IMG}/ampoule.jpg",
        },
        {
            "title": "Tenseloid",
            "body": "Крем на пептидах и коллагеновом комплексе — упругость и антивозрастной фокус.",
            "image": f"{TTT_IMG}/tenseloid.jpg",
        },
        {
            "title": "Intensive Care",
            "body": "Линии для салона и дома: концентрация, которую выбирают специалисты.",
            "image": f"{TTT_IMG}/care.jpg",
        },
    ],
    "partnership_title": "Эксклюзив для России и СНГ",
    "partnership": (
        "EvaCode и TOM-TIT-TOT подписали соглашение об эксклюзивной дистрибуции "
        "на рынках России и СНГ: прямая поставка, оригинальный уход и общая ответственность "
        "за то, как бренд появляется у клиента."
    ),
    "gallery": [
        {
            "image": f"{SIGNING_IMG}/signing-1.jpg",
            "alt": "Подписание соглашения EvaCode и TOM-TIT-TOT",
        },
        {
            "image": f"{SIGNING_IMG}/signing-2.jpg",
            "alt": "Эксклюзивное соглашение TOM-TIT-TOT для России и СНГ",
        },
        {
            "image": f"{SIGNING_IMG}/signing-meeting.jpg",
            "alt": "Встреча EvaCode и команды бренда",
        },
    ],
    "video_title": "",
}

TOM_TIT_TOT_TITLE_Q = (
    Q(title__icontains="tom-tit-tot")
    | Q(title__icontains="tom tit tot")
    | Q(title__icontains="(ttt)")
)


def ensure_tom_tit_tot_brand(*, link_goods: bool = True) -> ProductBrand:
    return _upsert_brand_page(TOM_TIT_TOT_PAGE, title_q=TOM_TIT_TOT_TITLE_Q, link_goods=link_goods)
