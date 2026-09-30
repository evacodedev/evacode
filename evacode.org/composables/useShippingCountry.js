const STORAGE_KEY = 'evacode_ship_country'

export function normalizeCountryCode(value) {
  const code = String(value || '').trim().toUpperCase()
  return /^[A-Z]{2}$/.test(code) ? code : ''
}

export const useShippingCountry = () => {
  const country = useState('shipping-country', () => '')

  function load() {
    if (!process.client || country.value) {
      return
    }
    try {
      country.value = normalizeCountryCode(localStorage.getItem(STORAGE_KEY))
    } catch (error) {
      country.value = ''
    }
  }

  function setCountry(value) {
    const code = normalizeCountryCode(value)
    country.value = code
    if (!process.client) {
      return
    }
    try {
      if (code) {
        localStorage.setItem(STORAGE_KEY, code)
      } else {
        localStorage.removeItem(STORAGE_KEY)
      }
    } catch (error) {
      return
    }
  }

  return { country, load, setCountry }
}
