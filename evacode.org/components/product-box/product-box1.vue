<template>
  <div>
    <div class="img-wrapper">
      <div class="lable-block">
        <span class="lable3" v-if="product.new">Новый</span>
        <span class="lable4" v-if="product.sale">sale</span>
      </div>
      <nuxt-link :class="'product-detail-link'" :to="{ path: '/product/sidebar/'+product.id}" @click="rememberProduct">
        <img
            ref="productImage"
            :src='imageSrc ? imageSrc : product.images[0].url'
            :id="product.id"
            class="img-fluid bg-img media"
            :class="{ 'is-loaded': imageLoaded }"
            :alt="product.title"
            :key="index"
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
  props: ['product', 'index'],
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
    }
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
  mounted() {
    const img = this.$refs.productImage
    if (img && img.complete && img.naturalWidth) {
      this.imageLoaded = true
    }
  },
  watch: {
    index() {
      this.imageLoaded = false
    },
  },
}
</script>
