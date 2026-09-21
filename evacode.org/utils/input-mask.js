import { parsePhoneNumberFromString } from 'libphonenumber-js'

export const PHONE_PREFERRED_COUNTRIES = [
  'KR',
  'RU',
  'KZ',
  'BY',
  'UA',
  'UZ',
  'US',
  'JP',
  'CN',
  'DE',
  'GB',
  'FR',
  'AE',
  'TH',
  'VN',
  'SG',
]

export function toIntlPhone(value) {
  const raw = String(value || '').trim()
  if (!raw) {
    return ''
  }
  const parsed =
    parsePhoneNumberFromString(raw) ||
    parsePhoneNumberFromString(raw.startsWith('+') ? raw : `+${raw.replace(/\D/g, '')}`)
  if (parsed) {
    return parsed.number
  }
  const digits = raw.replace(/\D/g, '')
  if (digits.length === 11 && digits.startsWith('8')) {
    const ru = parsePhoneNumberFromString(`+7${digits.slice(1)}`)
    if (ru) {
      return ru.number
    }
  }
  return raw
}

export function maskPhoneRu(value) {
  const digits = String(value || '').replace(/\D/g, '')
  if (!digits) {
    return ''
  }
  let rest = digits
  if (rest.startsWith('8')) {
    rest = rest.slice(1)
  } else if (rest.startsWith('7')) {
    rest = rest.slice(1)
  }
  rest = rest.slice(0, 10)
  let out = '+7'
  if (rest.length) {
    out += ` ${rest.slice(0, 3)}`
  }
  if (rest.length > 3) {
    out += `-${rest.slice(3, 6)}`
  }
  if (rest.length > 6) {
    out += `-${rest.slice(6, 8)}`
  }
  if (rest.length > 8) {
    out += `-${rest.slice(8, 10)}`
  }
  return out
}

export function maskTelegram(value) {
  const raw = String(value || '').replace(/[^a-zA-Z0-9_]/g, '')
  if (!raw) {
    return ''
  }
  return `@${raw.slice(0, 32)}`
}
