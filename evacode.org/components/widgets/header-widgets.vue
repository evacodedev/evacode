<template>
  <div class="shopping-cart-container">
    <div class="icon-nav">
      <ul class="header-tools">
        <li>
          <WidgetsContactPhone />
        </li>
        <li>
          <nuxt-link
            :to="accountTo"
            class="header-account"
            :class="{ 'is-signed-in': isLoggedIn }"
            :aria-label="accountLabel"
          >
            <div class="top-header-shopping-cart">
              <span class="header-account__icon">
                <svg
                  v-if="isLoggedIn"
                  class="img-fluid"
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <circle cx="12" cy="8" r="4.5" />
                  <path d="M4.2 20.2C5.7 17.2 8.6 15.3 12 15.3s6.3 1.9 7.8 4.9c.12.24-.03.55-.3.62A18.4 18.4 0 0112 21.3a18.4 18.4 0 01-7.5-.48c-.27-.07-.42-.38-.3-.62Z" />
                </svg>
                <img
                  v-else
                  alt=""
                  src="/images/new_evacode/account.svg"
                  class="img-fluid"
                >
                <span v-if="isLoggedIn" class="header-account__dot" />
              </span>
              <span class="shopping-cart-text">{{ accountLabel }}</span>
            </div>
          </nuxt-link>
        </li>
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
import { useAuthStore } from '~/store/auth'
import { useCartStore } from '~/store/cart'
import { mapState } from 'pinia'

export default {
  computed: {
    ...mapState(useCartStore, {
      drawerOpen: (store) => store.drawerOpen,
    }),
    ...mapState(useAuthStore, {
      isLoggedIn: 'isLoggedIn',
    }),
    cart() {
      return useCartStore().cartItems
    },
    accountLabel() {
      return this.isLoggedIn ? 'Кабинет' : 'Войти'
    },
    accountTo() {
      return this.isLoggedIn ? '/account/' : '/account/login/'
    },
  },
  methods: {
    toggleDrawer() {
      useCartStore().toggleDrawer()
    },
  },
}
</script>
