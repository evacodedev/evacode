<template>
  <div class="shopping-cart-container">
    <div class="icon-nav">
      <ul>
        <li class="onhover-div">
          <div>
            <div class="top-header-shopping-cart">
              <img alt src="/images/new_evacode/shopping-cart.svg" class="img-fluid">
              <span class="shopping-cart-text">Корзина</span>
            </div>
            <span class="cart_qty_cls">{{ cart.length }}</span>
          </div>
          <ul class="show-div shopping-cart" v-if="!cart.length">
            <li>Ваша корзина пуста.</li>
          </ul>
          <ul class="show-div shopping-cart" v-if="cart.length">
            <li v-for="(item,index) in cart" :key="index">
              <div class="media">
                <nuxt-link :to="{ path: '/product/sidebar/'+item.id}">
                  <img alt class="mr-3" :src='item.images[0].url'>
                </nuxt-link>
                <div class="media-body">
                  <nuxt-link :to="{ path: '/product/sidebar/'+item.id}">
                    <h4>{{ item.title }}</h4>
                  </nuxt-link>
                  <h4>
                    <span>{{ item.quantity }} x {{ getPrice(item.retail_price) }}<del>{{ getPrice(item.official_price) }}</del></span>
                  </h4>
                </div>
              </div>
              <div class="close-circle">
                <a href="#" @click='removeCartItem(item)'>
                  <i class="fa fa-times" aria-hidden="true"></i>
                </a>
              </div>
            </li>
            <li>
              <div class="total">
                <h5>
                  Итого :
                  <span>{{ getPrice(cartTotal) }}<del>{{ getPrice(cartOfficialTotal) }}</del></span>
                </h5>
              </div>
            </li>
            <li>
              <div class="buttons">
                <nuxt-link :to="{ path: '/page/account/cart'}" :class="'view-cart'">
                  В корзину
                </nuxt-link>
                <nuxt-link :to="{ path: '/page/account/checkout'}" :class="'checkout'">
                  Оформить
                </nuxt-link>
              </div>
            </li>
          </ul>
        </li>
      </ul>
    </div>
  </div>
</template>
<script>
import {useProductStore} from '~/store/products'
import {useCartStore} from '~/store/cart'
import {mapState} from 'pinia'

export default {
  computed: {
    ...mapState(useCartStore, {
      cartTotal: (store) => store.cartTotalAmount,
      cartOfficialTotal:(store) => store.cartTotalOfficialAmount,
    }),
    cart() {
      return useCartStore().cartItems
    },
    curr() {
      return useProductStore().changeCurrency
    }

  },
  watch: {
    cart() {
      useCartStore().cartItems
    },
  },
  methods: {
    removeCartItem: function (product) {
      useCartStore().removeCartItem(product)
      if (this.cart.length === 0 && this.$route.name === 'page-account-checkout') {
        this.$router.replace('/page/account/cart')
      }
    },
    getPrice: function (price) {
      return useProductStore().getPrice(price);
    }
  },
}
</script>
