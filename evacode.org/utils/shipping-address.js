// Строка адреса уходит без правок в Business.Ru, письмо клиенту и на EMS-этикетку.
// Для всех направлений EMS (включая СНГ) — латиница, страна по-английски.
const HOUSE_FIRST_DESTINATIONS = new Set(['US', 'GB', 'FR'])
const NON_LATIN_LETTER = /[^\P{L}\p{Script=Latin}]/u

export const OTHER_COUNTRY_CODE = 'EU'
// Тарифа EMS внутри Кореи нет: такой заказ оформляется как самовывоз.
export const KOREA_CODE = 'KR'
export const LATIN_ONLY_MESSAGE = 'Только латиницей (английскими буквами)'

function clean(value) {
  return String(value || '').trim()
}

function normalizeCode(code) {
  return clean(code).toUpperCase()
}

export function usesLatinAddress(code) {
  const value = normalizeCode(code)
  return Boolean(value) && value !== KOREA_CODE
}

export function hasNonLatinLetters(text) {
  return NON_LATIN_LETTER.test(String(text || ''))
}

// Русский, украинский, белорусский, казахский → ASCII-латиница для этикетки EMS.
const CYRILLIC_TO_LATIN = {
  а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', е: 'e', ё: 'e', ж: 'zh', з: 'z', и: 'i',
  й: 'y', к: 'k', л: 'l', м: 'm', н: 'n', о: 'o', п: 'p', р: 'r', с: 's', т: 't',
  у: 'u', ф: 'f', х: 'kh', ц: 'ts', ч: 'ch', ш: 'sh', щ: 'shch', ъ: '', ы: 'y', ь: '',
  э: 'e', ю: 'yu', я: 'ya',
  є: 'ye', і: 'i', ї: 'yi', ґ: 'g', ў: 'u',
  ә: 'a', ғ: 'g', қ: 'k', ң: 'n', ө: 'o', ұ: 'u', ү: 'u', һ: 'h',
}
const CYRILLIC_LETTER = /\p{Script=Cyrillic}/u

function isUpper(char) {
  return Boolean(char) && char !== char.toLowerCase()
}

export function transliterateCyrillic(text) {
  const source = String(text || '')
  if (!CYRILLIC_LETTER.test(source)) {
    return source
  }
  let result = ''
  for (let i = 0; i < source.length; i += 1) {
    const char = source[i]
    const latin = CYRILLIC_TO_LATIN[char.toLowerCase()]
    if (latin === undefined) {
      result += char
    } else if (!isUpper(char) || !latin) {
      result += latin
    } else {
      // «ЩУКА» → SHCHUKA, «Щука» → Shchuka
      const next = source[i + 1] || ''
      const allCaps = isUpper(next) || (!/\p{L}/u.test(next) && isUpper(source[i - 1]))
      result += allCaps ? latin.toUpperCase() : latin[0].toUpperCase() + latin.slice(1)
    }
  }
  return result
}

export function countryNameForLabel(code, fallback = '') {
  const value = normalizeCode(code)
  if (!usesLatinAddress(value) || value === OTHER_COUNTRY_CODE) {
    return fallback
  }
  try {
    return new Intl.DisplayNames(['en'], { type: 'region' }).of(value) || fallback
  } catch {
    return fallback
  }
}

export function formatAddressLine({ code, region, street, house, apartment, privateHouse }) {
  const value = normalizeCode(code)
  const flat = privateHouse ? '' : clean(apartment)
  const streetParts = HOUSE_FIRST_DESTINATIONS.has(value)
    ? [clean(house), clean(street)]
    : [clean(street), clean(house)]
  return [
    clean(region),
    streetParts.filter(Boolean).join(' '),
    flat ? `Apt. ${flat}` : '',
  ]
    .filter(Boolean)
    .join(', ')
}
