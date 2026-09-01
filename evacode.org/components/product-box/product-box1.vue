<template>
  <div>
    <div class="img-wrapper">
      <div class="lable-block">
        <span class="lable3" v-if="product.new">Новый</span>
        <span class="lable4" v-if="product.sale">sale</span>
      </div>
      <nuxt-link :class="'product-detail-link'" :to="{ path: '/product/sidebar/'+product.id}" @click="rememberProduct">
        <NuxtImg
            v-if="cardImageSrc"
            :src="cardImageSrc"
            :alt="product.title"
            :width="800"
            fit="inside"
            format="webp"
            :quality="75"
            densities="x1"
            :loading="index < 4 ? 'eager' : 'lazy'"
            :preload="index === 0"
            class="img-fluid bg-img media"
            :class="{ 'is-loaded': imageLoaded }"
            :key="cardImageSrc"
            @load="imageLoaded = true"
        />
      </nuxt-link>
    </div>
    <div class="product-detail">
      <nuxt-link :to="{ path: '/product/sidebar/'+product.id}" @click="rememberProduct">
        <h6>{{ product.title }}</h6>
      </nuxt-link>
      <h4>
       {{ getPrice(product.retail_price) }}
        <del>{{ getPrice(product.official_price) }}</del>
      </h4>
    </div>
    <div class="product-right">
      <div class="product-buttons">
        <button
            data-toggle="modal"
            data-target="#modal-cart"
            class="evacode-btn buy-btn btn-bordered"
            title="Купить"
            @click="addToCart(product, 1)"
            :disabled="1 > product.stock">Купить
        </button>
    </div>
    </div>
  </div>
</template>

<script>
import {mapState} from 'pinia'
import {useProductStore} from '~~/store/products'
import {useCartStore} from '~~/store/cart'

export default {
  props: {
    product: { type: Object, required: true },
    index: { type: Number, default: 0 },
  },
  data() {
    return {
      _imageSrc: '',
      cartProduct: {},
      cartval: false,
      imageLoaded: false,
    }
  },
  emits: ['opencartmodel'],
  computed: {
    curr() {
      return useProductStore().changeCurrency
    },
    imageSrc() {
      const isImageFromProduct =
          this.product.images &&
          this.product.images.length &&
          this.product.images.map((image)=>image.url).indexOf(this._imageSrc) !== -1;
      return isImageFromProduct ? this._imageSrc : '';
    },
    cardImageSrc() {
      if (this.imageSrc) {
        return this.imageSrc;
      }
      const images = this.product?.images;
      if (!images?.length) {
        return '';
      }
      return images[0].url || '';
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
  watch: {
    cardImageSrc() {
      this.imageLoaded = false
    },
  },
}
</script>
