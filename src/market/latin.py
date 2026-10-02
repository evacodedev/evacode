"""Имя и адрес в заказе — только латиница (этикетка EMS). Зеркало `utils/shipping-address.js`."""

import unicodedata

LATIN_ONLY_MESSAGE = "Только латиницей (английскими буквами)"

CYRILLIC_TO_LATIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
    "є": "ye", "і": "i", "ї": "yi", "ґ": "g", "ў": "u",
    "ә": "a", "ғ": "g", "қ": "k", "ң": "n", "ө": "o", "ұ": "u", "ү": "u", "һ": "h",
}


def _is_cyrillic(ch: str) -> bool:
    return "CYRILLIC" in unicodedata.name(ch, "")


def has_non_latin_letters(text) -> bool:
    return any(ch.isalpha() and not unicodedata.name(ch, "").startswith("LATIN ") for ch in str(text or ""))


def transliterate_cyrillic(text) -> str:
    source = str(text or "")
    if not any(_is_cyrillic(ch) for ch in source):
        return source
    result = []
    for i, ch in enumerate(source):
        latin = CYRILLIC_TO_LATIN.get(ch.lower())
        if latin is None:
            result.append(ch)
        elif not ch.isupper() or not latin:
            result.append(latin)
        else:
            # «ЩУКА» → SHCHUKA, «Щука» → Shchuka
            nxt = source[i + 1] if i + 1 < len(source) else ""
            prev = source[i - 1] if i > 0 else ""
            all_caps = nxt.isupper() or (not nxt.isalpha() and prev.isupper())
            result.append(latin.upper() if all_caps else latin[0].upper() + latin[1:])
    return "".join(result)
