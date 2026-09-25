<template>
  <div class="evacode-slide slide-6">
    <img
      class="slide-main-image"
      src="/images/new_evacode/Slides/slide_6.webp"
      alt="CH6 — сыворотка для волос"
      width="1920"
      height="600"
      loading="lazy"
    >
    <div class="row">
      <div class="col">
        <div class="slider-container">
          <WidgetsBrandLogo />
          <p class="slider-headline">CH6 Сыворотка для волос</p>
          <p class="slider-description">Функциональная сыворотка-эссенция для кожи головы, которая помогает облегчить симптомы выпадения волос и ускоряет рост волос.</p>
          <p v-if="product" class="slider-headline slider-price">{{ getPrice(product.retail_price) }}</p>
          <nuxt-link :to="{ path: `/product/${productId}` }" class="evacode-btn slider-btn" @click="rememberProduct">Купить</nuxt-link>
        </div>
      </div>
    </div>
    <div class="container">
      <div class="row">
        <div class="col">
          <div class="slider-container">
            <p class="slider-headline">CH6 Сыворотка для волос</p>
            <p v-if="product" class="slider-headline slider-price">{{ getPrice(product.retail_price) }}</p>
            <nuxt-link :to="{ path: `/product/${productId}` }" class="evacode-btn slider-btn btn-bordered" @click="rememberProduct">Купить</nuxt-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {useProductStore} from '~/store/products';
const productId = 860261;
const {data: productResponse} = await useAsyncData(
    `slide-product-${productId}`,
    () => $fetch(`${useRuntimeConfig().public.apiBase}/market/goods`, {
        query: {
            id: productId,
        }
    }),
);

const product = computed(() => productResponse.value?.results[0]);
const rememberProduct = () => {
    if (product.value) {
        useProductPreview().setPreview(product.value);
    }
};

const getPrice = (price) => {
    return useProductStore().getPrice(price);
};
</script>
