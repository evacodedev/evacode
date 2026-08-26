<template>
  <div class="evacode-slide slide-6">
    <img class="slide-main-image" src="/images/new_evacode/Slides/slide_6.jpg" alt="">
    <div class="row">
      <div class="col">
        <div class="slider-container">
          <WidgetsBrandLogo />
          <h1 class="slider-headline">CH6 Сыворотка для волос</h1>
          <p class="slider-description">Функциональная сыворотка-эссенция для кожи головы, которая помогает облегчить симптомы выпадения волос и ускоряет рост волос.</p>
          <p v-if="product" class="slider-headline slider-price">{{ getPrice(product.retail_price) }}</p>
          <nuxt-link :to="{ path: `/product/sidebar/${productId}` }" class="evacode-btn slider-btn">Купить</nuxt-link>
        </div>
      </div>
    </div>
    <div class="container">
      <div class="row">
        <div class="col">
          <div class="slider-container">
            <h1 class="slider-headline">CH6 Сыворотка для волос</h1>
            <p v-if="product" class="slider-headline slider-price">{{ getPrice(product.retail_price) }}</p>
            <nuxt-link :to="{ path: `/product/sidebar/${productId}` }" class="evacode-btn slider-btn btn-bordered">Купить</nuxt-link>
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
    'productResponse',
    () => $fetch(`${useRuntimeConfig().public.apiBase}/market/goods`, {
        query: {
            id: productId,
        }
    }),
    {
        server: false,
    }
);

const product = computed(() => productResponse.value?.results[0]);

const getPrice = (price) => {
    return useProductStore().getPrice(price);
};
</script>
