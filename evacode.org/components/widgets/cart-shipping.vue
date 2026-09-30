<template>
  <div class="cart-shipping">
    <h2 class="cart-shipping__title">Доставка</h2>
    <CheckoutField
      :model-value="country"
      name="cart-country"
      label="Страна доставки"
      autocomplete="country"
      :options="countryOptions"
      @update:model-value="$emit('update:country', $event)"
    />

    <dl class="cart-shipping__lines">
      <div class="cart-shipping__line">
        <dt>Товары</dt>
        <dd>{{ getPrice(goodsTotal) }}</dd>
      </div>
      <div class="cart-shipping__line">
        <dt>
          {{ isPickup ? 'Самовывоз в Корее' : 'Доставка EMS' }}
          <span v-if="weightText" class="cart-shipping__weight">{{ weightText }}</span>
        </dt>
        <dd>{{ shippingText }}</dd>
      </div>
      <div class="cart-shipping__line cart-shipping__line--total">
        <dt>Итого с доставкой</dt>
        <dd>{{ shippingKrw == null ? '—' : getPrice(goodsTotal + shippingKrw) }}</dd>
      </div>
    </dl>
    <p v-if="error" class="cart-shipping__note cart-shipping__note--error">{{ error }}</p>
    <p v-else-if="isPickup" class="cart-shipping__note">
      По Корее EMS не отправляем — заказ можно забрать самовывозом.
    </p>
  </div>
</template>

<script setup>
import { useProductStore } from '~~/store/products'
import { addressCountryOptions } from '~/utils/account-address'
import { KOREA_CODE } from '~/utils/shipping-address'

const props = defineProps({
  items: { type: Array, default: () => [] },
  goodsTotal: { type: Number, default: 0 },
  country: { type: String, default: '' },
})
defineEmits(['update:country'])

const productStore = useProductStore()
const apiBase = useRuntimeConfig().public.apiBase

const destinations = ref([])
const shippingKrw = ref(null)
const chargeableGrams = ref(null)
const loading = ref(false)
const error = ref('')
let timer = null
let requestId = 0

const countryOptions = computed(() => addressCountryOptions(destinations.value))
const isPickup = computed(() => props.country === KOREA_CODE)

const shippingText = computed(() => {
  if (!props.country) {
    return 'Выберите страну'
  }
  if (loading.value) {
    return 'Считаем…'
  }
  if (shippingKrw.value == null) {
    return '—'
  }
  return shippingKrw.value === 0 ? 'Бесплатно' : getPrice(shippingKrw.value)
})

const weightText = computed(() => {
  if (!props.country || isPickup.value || !chargeableGrams.value) {
    return ''
  }
  const kg = (chargeableGrams.value / 1000).toLocaleString('ru-RU', { maximumFractionDigits: 1 })
  return `· ${kg} кг с упаковкой`
})

function getPrice(price) {
  return productStore.getPrice(price)
}

async function loadDestinations() {
  try {
    const data = await $fetch(`${apiBase}/market/shipping/destinations/`)
    destinations.value = data?.results || []
  } catch (err) {
    destinations.value = []
  }
}

async function fetchQuote() {
  const current = ++requestId
  error.value = ''
  if (!props.country || !props.items.length) {
    shippingKrw.value = null
    return
  }
  loading.value = true
  try {
    const data = await $fetch(`${apiBase}/market/shipping/quote/`, {
      method: 'POST',
      body: {
        cart: props.items.map((item) => ({ id: item.id, quantity: item.quantity })),
        shipping: isPickup.value
          ? { method: 'pickup', destination: KOREA_CODE }
          : { method: 'ems', destination: props.country },
      },
    })
    if (current !== requestId) {
      return
    }
    shippingKrw.value = data?.shipping_krw ?? null
    chargeableGrams.value = data?.chargeable_weight_grams ?? null
  } catch (err) {
    if (current !== requestId) {
      return
    }
    shippingKrw.value = null
    chargeableGrams.value = err?.data?.chargeable_weight_grams ?? null
    error.value = err?.data?.error || 'Не удалось посчитать доставку. Точную сумму покажем при оформлении.'
  } finally {
    if (current === requestId) {
      loading.value = false
    }
  }
}

function scheduleQuote() {
  clearTimeout(timer)
  timer = setTimeout(fetchQuote, 250)
}

watch(
  () => [props.country, props.items.map((item) => `${item.id}-${item.quantity}`).join(',')],
  scheduleQuote,
)

onMounted(() => {
  loadDestinations()
  fetchQuote()
})
onBeforeUnmount(() => clearTimeout(timer))
</script>
