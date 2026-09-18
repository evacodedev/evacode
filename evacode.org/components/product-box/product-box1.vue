<template>
  <div class="product-card" :class="{ 'is-in-cart': inCart }">
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
      <span v-if="inCart" class="product-card__in-cart" aria-hidden="true">В корзине</span>
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
          class="evacode-btn buy-btn btn-bordered"
          :class="{ 'is-in-cart': inCart }"
          :title="inCart ? 'Добавить ещё' : 'В корзину'"
          @click="addToCart(product)"
          :disabled="1 > product.stock"
      >{{ inCart ? 'В корзине' : 'В корзину' }}</button>
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
      imageLoaded: true,
    }
  },
  computed: {
    ...mapState(useCartStore, {
      cartItems: (store) => store.cartItems,
    }),
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
    inCart() {
      const id = this.product && this.product.id
      if (id == null) {
        return false
      }
      return this.cartItems.some((item) => item.id === id)
    },
  },
  methods: {
    rememberProduct() {
      useProductPreview().setPreview(this.product)
      useCatalogReturn().rememberFromCatalog({
        path: useRoute().fullPath,
        productId: this.product && this.product.id,
        scrollY: import.meta.client ? window.scrollY : 0,
      })
    },
    addToCart(product) {
      useCartStore().addToCart(product)
    },
    productVariantChange(imgsrc) {
      this._imageSrc = imgsrc
    },
    getPrice(price) {
      return useProductStore().getPrice(price);
    }
  },
}
</script>
