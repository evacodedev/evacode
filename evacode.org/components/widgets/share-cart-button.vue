<template>
  <div ref="root" class="share-cart">
    <button
      type="button"
      class="share-cart__btn"
      aria-label="Поделиться корзиной"
      title="Поделиться корзиной"
      @click="share"
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="18" cy="5" r="2.6" />
        <circle cx="6" cy="12" r="2.6" />
        <circle cx="18" cy="19" r="2.6" />
        <path d="M8.3 13.3l7.4 4.4M15.7 6.3l-7.4 4.4" />
      </svg>
      <span class="share-cart__label">Поделиться</span>
    </button>
    <div v-if="status" class="share-cart__popover" role="status">
      <p class="share-cart__status">{{ status }}</p>
      <input
        v-if="fallbackUrl"
        class="share-cart__url"
        type="text"
        readonly
        :value="fallbackUrl"
        aria-label="Ссылка на корзину"
        @focus="$event.target.select()"
      >
    </div>
  </div>
</template>

<script setup>
import { useCartStore } from '~~/store/cart'

const cartStore = useCartStore()
const { country, load: loadCountry } = useShippingCountry()
const root = ref(null)
const status = ref('')
const fallbackUrl = ref('')
let hideTimer = null

function reset() {
  clearTimeout(hideTimer)
  status.value = ''
  fallbackUrl.value = ''
}

function onOutsideClick(event) {
  if (status.value && root.value && !root.value.contains(event.target)) {
    reset()
  }
}

watch(() => cartStore.cart, reset, { deep: true })

onMounted(() => document.addEventListener('click', onOutsideClick))
onBeforeUnmount(() => {
  document.removeEventListener('click', onOutsideClick)
  clearTimeout(hideTimer)
})

async function share() {
  loadCountry()
  const url = sharedCartUrl(window.location.origin, cartStore.cart, country.value)
  if (!url) {
    return
  }
  reset()
  if (navigator.share && window.matchMedia('(pointer: coarse)').matches) {
    try {
      await navigator.share({ title: 'Моя корзина Evacode', url })
      return
    } catch (error) {
      if (error?.name === 'AbortError') {
        return
      }
    }
  }
  try {
    await navigator.clipboard.writeText(url)
    status.value = 'Ссылка на корзину скопирована — отправьте её консультанту.'
    hideTimer = setTimeout(reset, 4000)
  } catch (error) {
    status.value = 'Скопируйте ссылку на корзину:'
    fallbackUrl.value = url
  }
}
</script>
