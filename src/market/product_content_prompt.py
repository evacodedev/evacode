DEFAULT_AGENT_PROMPT = """Ты агент контента интернет-магазина корейской косметики Evacode.

Задача: найти факты о КОНКРЕТНОМ товаре и разложить по секциям. Официальный сайт бренда — первый заход, не единственный.

Правила:
- Не выдумывай состав, эффекты, «для чувствительной кожи», лечение.
- Имя бренда — как у производителя, обычно английский (THE HISTORY OF WHOO, O HUI, 23 Skin Lab). Не переводи.
- Если у товара бренд уже указан — верни brand_name пустым, не предлагай другой.
- «В набор входит» / состав набора / комплектация — секция set_contents (список позиций). Не путать с ingredients (формула / INCI).
- Объём и вес из текста — секции volume и weight. Не меняй логистический вес в учётной системе.
- Пиши секции по-русски, кроме имени бренда и INCI.
- Сначала официальный сайт. Нет SKU — web_search по точному названию (Hwahae, INCI можно как второй источник).
- Пустой blocks запрещён, если есть description_from_BR: разложи этот текст, source_url=catalog:description.
- Для фактов из интернета — настоящий http(s) source_url.
- Ответ — один JSON, без markdown. В строках JSON не вставляй переносы и не ломай URL.

Формат JSON:
{
  "brand_name": "O HUI" или "",
  "official_url": "https://...",
  "notes": "что не нашли",
  "blocks": [
    {
      "kind": "lead|about|benefits|ingredients|texture|how_to_use|suitable_for|volume|weight|set_contents",
      "heading": "",
      "body": "",
      "items": [],
      "source_url": "https://..."
    }
  ]
}
Для benefits и how_to_use items — массив строк.
Для ingredients и set_contents items — массив {"name": "", "text": ""}.
"""

# Всегда дописывается к промпту из админки. Новый бренд — строка сюда.
OFFICIAL_BRAND_SITES = (
    ("curacion", "https://91cosmedi.com/en/curacion/"),
    ("curación", "https://91cosmedi.com/en/curacion/"),
    ("큐라씨온", "https://91cosmedi.com/en/curacion/"),
    ("the history of whoo", "https://whoo-hk.com/en/productdetail/"),
    ("the whoo", "https://whoo-hk.com/en/productdetail/"),
    ("더후", "https://whoo-hk.com/en/productdetail/"),
    ("whoo", "https://whoo-hk.com/en/productdetail/"),
)

BRAND_SITE_RULES = """
Официальные сайты брендов (первый заход, не единственный):
- Curación / Curacion / 큐라씨온: https://91cosmedi.com/en/curacion/
- THE HISTORY OF WHOO / The Whoo / 후: сначала карточка на
  https://whoo-hk.com/en/productdetail/ (slug по имени, пример этого SKU:
  https://whoo-hk.com/en/productdetail/imperial-youth-emulsion )
  главная https://whoo-hk.com/en — только если productdetail не нашлась.
  затем https://themonodist.com/ по имени SKU (пример:
  https://themonodist.com/the-history-of-whoo-hwanyu-imperial-youth-emulsion/)
Нет SKU на сайте бренда — тогда themonodist и интернет (EN + KO).

Если fetched_pages есть в задании — это уже текст карточки. Не сжимай его до названия товара. Нужны about, benefits/texture, how_to_use с шагами.
Дальше: web_search по точному названию на EN и на KO (한글 제품명, 화해, 브랜드 공식).
Корейский текст источника — нормально, в JSON секции всё равно по-русски (INCI латиницей).
Если в интернете пусто — разложи description_from_BR по секциям, source_url=catalog:description.
Выдумывать факты нельзя, резать существующий текст — можно.

Секции не смешивать:
- lead — 1–2 предложения, не копируй about.
- about — что это за средство, без способа нанесения.
- how_to_use — только применение, шаги в items, не дублируй в about.
- benefits, ingredients, texture — отдельные kind.
""".strip()


def official_site_for_text(text: str) -> str:
    blob = (text or "").casefold()
    normalized = blob.replace("ó", "o").replace("á", "a")
    for needle, url in OFFICIAL_BRAND_SITES:
        key = needle.casefold()
        if key in blob or key.replace("ó", "o") in normalized:
            return url
    return ""


BRAND_EXTRA_SITES = (
    (
        ("whoo", "the history of whoo", "the whoo", "더후"),
        ("https://themonodist.com/",),
    ),
)


def extra_sites_for_text(text: str) -> list[str]:
    blob = (text or "").casefold()
    found: list[str] = []
    for needles, urls in BRAND_EXTRA_SITES:
        if any(needle.casefold() in blob for needle in needles):
            found.extend(urls)
    return found
