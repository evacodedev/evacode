<template>
  <div class="shopping-cart-container">
    <div class="icon-nav">
      <ul>
        <li class="cart-drawer-trigger-wrap">
          <button
            type="button"
            class="cart-drawer-trigger"
            :aria-expanded="drawerOpen ? 'true' : 'false'"
            aria-controls="cart-drawer-title"
            aria-label="Открыть корзину"
            @click="toggleDrawer"
          >
            <div class="top-header-shopping-cart">
              <img alt="" src="/images/new_evacode/shopping-cart.svg" class="img-fluid">
              <span class="shopping-cart-text">Корзина</span>
            </div>
            <span class="cart_qty_cls">{{ cart.length }}</span>
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>
<script>
import { useCartStore } from '~/store/cart'
import { mapState } from 'pinia'

export default {
  computed: {
    ...mapState(useCartStore, {
      drawerOpen: (store) => store.drawerOpen,
    }),
    cart() {
      return useCartStore().cartItems
    },
  },
  methods: {
    toggleDrawer() {
      useCartStore().toggleDrawer()
    },
  },
}
</script>
