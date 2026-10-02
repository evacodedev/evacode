<template>
  <button
    type="button"
    :class="[buttonClass, { 'is-saved': saved, 'is-busy': busy }]"
    :aria-pressed="saved ? 'true' : 'false'"
    :aria-label="saved ? 'Убрать из избранного' : 'В избранное'"
    :disabled="busy"
    @click="onClick"
  >
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12 19.2s-6.2-3.9-6.2-8.1A3.7 3.7 0 0 1 12 7.5a3.7 3.7 0 0 1 6.2 3.6C18.2 15.3 12 19.2 12 19.2Z"
        stroke-linejoin="round"
      />
    </svg>
    <span v-if="showLabel">{{ saved ? 'В избранном' : 'В избранное' }}</span>
  </button>
</template>

<script setup>
import { useWishlistStore } from '~/store/wishlist'

const props = defineProps({
  product: { type: Object, required: true },
  buttonClass: { type: String, default: '' },
  showLabel: { type: Boolean, default: false },
})

const wishlist = useWishlistStore()
const busy = ref(false)
const saved = computed(() => wishlist.contains(props.product?.id))

const onClick = async () => {
  if (busy.value || props.product?.id == null) {
    return
  }
  busy.value = true
  try {
    await wishlist.toggle(props.product, useRoute().fullPath)
  } catch {
    // Сердце возвращается само: список откатился.
  } finally {
    busy.value = false
  }
}
</script>
