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
