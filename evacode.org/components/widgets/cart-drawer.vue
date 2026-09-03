<template>
  <ClientOnly>
    <Teleport to="body">
      <Transition name="soft-fade">
        <div
          v-if="drawerOpen"
          class="cart-drawer-overlay"
          @click="closeDrawer"
        />
      </Transition>
      <Transition name="cart-drawer-slide">
        <aside
          v-if="drawerOpen"
          class="cart-drawer"
          role="dialog"
          aria-modal="true"
          aria-labelledby="cart-drawer-title"
        >
          <header class="cart-drawer__header">
            <div class="cart-drawer__title-row">
              <h2 id="cart-drawer-title" class="cart-drawer__title">Корзина</h2>
              <span class="cart-drawer__count">{{ cartCount }}</span>
            </div>
            <button
              type="button"
              class="cart-drawer__close"
              aria-label="Закрыть корзину"
              @click="closeDrawer"
            >
              ×
            </button>
          </header>

          <div class="cart-drawer__body">
            <p v-if="!cart.length" class="cart-drawer__empty">Ваша корзина пуста.</p>
            <ul v-else class="cart-drawer__list">
              <li v-for="item in cart" :key="item.id" class="cart-drawer__item">
                <nuxt-link
                  class="cart-drawer__thumb"
                  :to="{ path: '/product/sidebar/' + item.id }"
                  @click="onProductClick(item)"
                >
                  <img
                    v-if="itemImage(item)"
                    :src="itemImage(item)"
                    :alt="item.title"
                  >
                </nuxt-link>
                <div class="cart-drawer__meta">
                  <div class="cart-drawer__item-top">
                    <nuxt-link
                      class="cart-drawer__name"
                      :to="{ path: '/product/sidebar/' + item.id }"
                      @click="onProductClick(item)"
                    >
                      {{ item.title }}
                    </nuxt-link>
                    <button
                      type="button"
                      class="cart-drawer__remove"
                      aria-label="Удалить из корзины"
                      @click="removeCartItem(item)"
                    >
                      ×
                    </button>
                  </div>
                  <p class="cart-drawer__price">
                    {{ getPrice(item.retail_price) }}
                    <del v-if="item.official_price && item.official_price > item.retail_price">
                      {{ getPrice(item.official_price) }}
                    </del>
                  </p>
                  <div class="cart-drawer__qty" role="group" aria-label="Количество">
                    <button
                      type="button"
                      class="cart-drawer__qty-btn"
                      :disabled="item.quantity <= 1"
                      aria-label="Уменьшить количество"
                      @click="decrement(item)"
                    >
                      −
                    </button>
                    <span class="cart-drawer__qty-value">{{ item.quantity }}</span>
                    <button
                      type="button"
                      class="cart-drawer__qty-btn"
                      aria-label="Увеличить количество"
                      @click="increment(item)"
                    >
                      +
                    </button>
                  </div>
                </div>
              </li>
            </ul>
          </div>

          <footer v-if="cart.length" class="cart-drawer__footer">
            <div class="cart-drawer__subtotal">
              <span>Сумма</span>
              <strong>{{ getPrice(cartTotal) }}</strong>
            </div>
            <p class="cart-drawer__note">Доставка рассчитывается при оформлении.</p>
            <nuxt-link
              to="/page/account/cart"
              class="evacode-btn cart-drawer__btn"
              @click="closeDrawer"
            >
              В корзину
            </nuxt-link>
            <nuxt-link
              to="/page/account/checkout"
              class="evacode-btn fill-btn cart-drawer__btn"
              @click="closeDrawer"
            >
              Оформить
            </nuxt-link>
          </footer>
        </aside>
      </Transition>
    </Teleport>
  </ClientOnly>
</template>

<script>
import { useProductStore } from '~/store/products'
import { useCartStore } from '~/store/cart'
import { mapState } from 'pinia'

export default {
  computed: {
    ...mapState(useCartStore, {
      cartTotal: (store) => store.cartTotalAmount,
      drawerOpen: (store) => store.drawerOpen,
    }),
    cart() {
      return useCartStore().cartItems
    },
    cartCount() {
      return this.cart.reduce((sum, item) => sum + (item.quantity || 0), 0)
    },
  },
  watch: {
    drawerOpen(open) {
      if (process.client) {
        document.documentElement.classList.toggle('cart-drawer-open', open)
      }
    },
    '$route.path'() {
      this.closeDrawer()
    },
  },
  mounted() {
    window.addEventListener('keydown', this.onKeydown)
  },
  beforeUnmount() {
    window.removeEventListener('keydown', this.onKeydown)
    document.documentElement.classList.remove('cart-drawer-open')
  },
  methods: {
    itemImage(item) {
      return item?.images?.[0]?.url || ''
    },
    closeDrawer() {
      useCartStore().closeDrawer()
    },
    onKeydown(event) {
      if (event.key === 'Escape') {
        this.closeDrawer()
      }
    },
    onProductClick(item) {
      useProductPreview().setPreview(item)
      this.closeDrawer()
    },
    increment(item) {
      useCartStore().updateCartQuantity({ product: item, qty: 1 })
    },
    decrement(item) {
      useCartStore().updateCartQuantity({ product: item, qty: -1 })
    },
    removeCartItem(item) {
      useCartStore().removeCartItem(item)
      if (this.cart.length === 0 && this.$route.name === 'page-account-checkout') {
        this.$router.replace('/page/account/cart')
      }
    },
    getPrice(price) {
      return useProductStore().getPrice(price)
    },
  },
}
</script>
