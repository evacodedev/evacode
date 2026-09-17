<template>
  <div class="product-card">
    <div class="img-wrapper">
      <div class="lable-block">
        <span class="lable3" v-if="product.new">Новый</span>
        <span class="lable4" v-if="product.sale">sale</span>
      </div>
      <nuxt-link class="product-detail-link" :to="{ path: '/product/' + product.id }" @click="rememberProduct">
        <img
            v-if="cardImageUrl"
            ref="productImage"
            :src="cardImageUrl"
            :id="product.id"
            class="img-fluid bg-img media"
            :class="{ 'is-loaded': imageLoaded, 'is-priority': isPriorityImage }"
            :alt="product.title"
            :key="product.id"
            width="720"
            height="720"
            decoding="async"
            :loading="isPriorityImage ? 'eager' : 'lazy'"
            :fetchpriority="isPriorityImage ? 'high' : 'auto'"
            sizes="(max-width: 767px) 50vw, (max-width: 1199px) 50vw, 30vw"
            @load="imageLoaded = true"
        />
      </nuxt-link>
    </div>
    <div class="product-detail">
      <nuxt-link :to="{ path: '/product/' + product.id }" @click="rememberProduct">
        <h6>{{ product.title }}</h6>
      </nuxt-link>
      <div v-if="cardExcerpt" class="product-card__excerpt">{{ cardExcerpt }}</div>
      <div class="product-card__prices">
        <span class="product-card__price">{{ getPrice(product.retail_price) }}</span>
        <del v-if="showOfficialPrice" class="product-card__was">{{ getPrice(product.official_price) }}</del>
      </div>
      <button
          type="button"
          data-toggle="modal"
          data-target="#modal-cart"
          class="evacode-btn buy-btn btn-bordered"
          title="Купить"
          @click="addToCart(product, 1)"
          :disabled="1 > product.stock"
      >Купить</button>
    </div>
  </div>
</template>

<script>
import {mapState} from 'pinia'
import {useProductStore} from '~~/store/products'
import {useCartStore} from '~~/store/cart'

export default {
  props: ['product', 'index'],
  data() {
    return {
      _imageSrc: '',
      cartProduct: {},
      cartval: false,
      imageLoaded: true,
    }
  },
  emits: ['opencartmodel'],
  computed: {
    curr() {
      return useProductStore().changeCurrency
    },
    isPriorityImage() {
      return Number(this.index) < 4
    },
    imageSrc() {
      const isImageFromProduct =
          this.product.images &&
          this.product.images.length &&
          this.product.images.map((image)=>image.url).indexOf(this._imageSrc) !== -1;
      return isImageFromProduct ? this._imageSrc : '';
    },
    cardImageUrl() {
      if (this.imageSrc) {
        return this.imageSrc
      }
      const first = this.product && this.product.images && this.product.images[0]
      return first && first.url ? first.url : ''
    },
    showOfficialPrice() {
      const official = Number(this.product && this.product.official_price)
      const retail = Number(this.product && this.product.retail_price)
      return Number.isFinite(official) && official > retail
    },
    cardExcerpt() {
      const text = this.product && this.product.excerpt
      return text ? String(text).trim() : ''
    },
  },
  methods: {
    rememberProduct() {
      useProductPreview().setPreview(this.product)
    },
    addToCart: function (product) {

      this.cartval = true
      this.cartProduct = product
      this.$emit('opencartmodel', this.cartval, this.cartProduct)

      useCartStore().addToCart(product)
    },
    productVariantChange(imgsrc) {
      this._imageSrc = imgsrc
    },
    getPrice: function (price) {
      return useProductStore().getPrice(price);
    }
  },
}
</script>
