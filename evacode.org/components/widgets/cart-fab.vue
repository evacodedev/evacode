<template>
  <ClientOnly>
    <Transition name="soft-fade">
      <button
        v-if="hasItems"
        type="button"
        class="cart-fab"
        :class="{ 'is-with-top': showTapTop }"
        aria-label="Открыть корзину"
        @click="openCart"
      >
        <img
          src="/images/new_evacode/shopping-cart.svg"
          alt=""
          class="cart-fab__icon"
          width="22"
          height="22"
        >
        <span class="cart-fab__label">Корзина</span>
        <span class="cart-fab__count">{{ itemCount }}</span>
      </button>
    </Transition>
  </ClientOnly>
</template>

<script>
import { useCartStore } from '~/store/cart'

export default {
  data() {
    return {
      showTapTop: false,
    }
  },
  computed: {
    cart() {
      return useCartStore().cartItems
    },
    hasItems() {
      return this.cart.length > 0
    },
    itemCount() {
      return this.cart.length
    },
  },
  methods: {
    openCart() {
      useCartStore().openDrawer()
    },
    onScroll() {
      this.showTapTop = window.scrollY > 600
    },
  },
  mounted() {
    this.onScroll()
    window.addEventListener('scroll', this.onScroll, { passive: true })
  },
  beforeUnmount() {
    window.removeEventListener('scroll', this.onScroll)
  },
}
</script>
