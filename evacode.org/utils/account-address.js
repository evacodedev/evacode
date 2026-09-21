export function emptyAccountAddress() {
  return {
    country: '',
    country_code: '',
    city: '',
    street: '',
    house: '',
    apartment: '',
    postal_code: '',
    comment: '',
  }
}

export function normalizeAddressList(data) {
  return Array.isArray(data) ? data : (data?.results || [])
}

export function addressCountryOptions(destinations) {
  const list = (destinations || []).map((item) => ({
    value: item.code,
    label: item.name,
  }))
  if (!list.some((item) => item.value === 'KR')) {
    list.unshift({ value: 'KR', label: 'Корея' })
  }
  return list
}

export function countryNameFromCode(destinations, code) {
  const match = addressCountryOptions(destinations).find((item) => item.value === code)
  return match?.label || ''
}

export function formatAccountAddress(item) {
  if (!item) {
    return ''
  }
  const parts = []
  if (item.country) {
    parts.push(item.country)
  }
  if (item.city) {
    parts.push(`г. ${item.city}`)
  }
  if (item.street) {
    parts.push(item.street)
  }
  if (item.house) {
    parts.push(`дом ${item.house}`)
  }
  if (item.apartment) {
    parts.push(`кв. ${item.apartment}`)
  } else {
    parts.push('частный дом')
  }
  if (item.postal_code) {
    parts.push(`индекс ${item.postal_code}`)
  }
  return parts.join(', ')
}

export function accountAddressPayload(fields) {
  return {
    country: String(fields.country || '').trim(),
    country_code: String(fields.country_code || '').trim().toUpperCase(),
    city: String(fields.city || '').trim(),
    street: String(fields.street || '').trim(),
    house: String(fields.house || '').trim(),
    apartment: String(fields.apartment || '').trim(),
    postal_code: String(fields.postal_code || '').trim(),
    comment: String(fields.comment || '').trim(),
  }
}

function addressPart(value) {
  return String(value || '').trim().toLowerCase()
}

export function sameAccountAddress(left, right) {
  if (!left || !right) {
    return false
  }
  if (addressPart(left.city) !== addressPart(right.city)) {
    return false
  }
  if (addressPart(left.street || left.address) !== addressPart(right.street || right.address)) {
    return false
  }
  if (addressPart(left.house) !== addressPart(right.house)) {
    return false
  }
  if (addressPart(left.apartment) !== addressPart(right.apartment)) {
    return false
  }
  if (addressPart(left.postal_code) !== addressPart(right.postal_code)) {
    return false
  }
  const leftCode = String(left.country_code || '').trim().toUpperCase()
  const rightCode = String(right.country_code || '').trim().toUpperCase()
  if (leftCode && rightCode && leftCode !== rightCode) {
    return false
  }
  return true
}
