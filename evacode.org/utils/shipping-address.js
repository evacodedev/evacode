// Строка адреса уходит без правок в Business.Ru, письмо клиенту и на EMS-этикетку.
const CYRILLIC_DESTINATIONS = new Set(['RU', 'KZ', 'KG', 'BY'])
const HOUSE_FIRST_DESTINATIONS = new Set(['US', 'GB', 'FR'])
const NON_LATIN_LETTER = /[^\P{L}\p{Script=Latin}]/u

export const OTHER_COUNTRY_CODE = 'EU'
export const LATIN_ONLY_MESSAGE = 'Латиницей, как на посылках в вашей стране'

function clean(value) {
  return String(value || '').trim()
}

function normalizeCode(code) {
  return clean(code).toUpperCase()
}

export function usesLatinAddress(code) {
  const value = normalizeCode(code)
  return Boolean(value) && value !== 'KR' && !CYRILLIC_DESTINATIONS.has(value)
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
  if (!usesLatinAddress(value)) {
    return [
      clean(region),
      clean(street),
      clean(house) ? `д. ${clean(house)}` : '',
      privateHouse ? 'частный дом' : (flat ? `кв. ${flat}` : ''),
    ]
      .filter(Boolean)
      .join(', ')
  }
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
