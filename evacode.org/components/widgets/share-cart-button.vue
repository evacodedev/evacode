<template>
  <div class="share-cart" :class="{ 'share-cart--block': block }">
    <button type="button" class="share-cart__button" @click="share">
      <i class="fa fa-share-alt" aria-hidden="true"></i>
      Поделиться корзиной
    </button>
    <p v-if="status" class="share-cart__status" role="status">{{ status }}</p>
    <p v-else-if="hint" class="share-cart__hint">{{ hint }}</p>
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
</template>

<script setup>
import { useCartStore } from '~~/store/cart'

defineProps({
  block: { type: Boolean, default: false },
  hint: { type: String, default: '' },
})

const cartStore = useCartStore()
const status = ref('')
const fallbackUrl = ref('')

watch(() => cartStore.cart, () => {
  status.value = ''
  fallbackUrl.value = ''
}, { deep: true })

async function share() {
  const url = sharedCartUrl(window.location.origin, cartStore.cart)
  if (!url) {
    return
  }
  fallbackUrl.value = ''
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
    status.value = 'Ссылка скопирована — вставьте её в чат с консультантом.'
  } catch (error) {
    status.value = 'Скопируйте ссылку:'
    fallbackUrl.value = url
  }
}
</script>
