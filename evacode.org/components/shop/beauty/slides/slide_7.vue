<template>
  <div class="evacode-slide slide-7">
    <img
      class="slide-main-image"
      src="/images/new_evacode/Slides/slide_7.webp"
      alt="Ритуал корейской красоты — крем и уход"
      width="1280"
      height="720"
      fetchpriority="high"
    >
    <div class="slide-7__veil" aria-hidden="true"></div>
    <div class="row">
      <div class="col">
        <div class="slider-container">
          <WidgetsBrandLogo />
          <h1 class="slider-headline">Ритуал корейской красоты</h1>
          <p class="slider-description">крем и уход от ведущих брендов</p>
          <nuxt-link :to="{ path: '/collection/leftsidebar/0' }" class="evacode-btn slider-btn">Каталог</nuxt-link>
        </div>
      </div>
    </div>
    <div class="container">
      <div class="row">
        <div class="col">
          <div class="slider-container">
            <p class="slider-headline">Ритуал корейской красоты</p>
            <p class="slider-description">крем и уход от ведущих брендов</p>
            <nuxt-link :to="{ path: '/collection/leftsidebar/0' }" class="evacode-btn slider-btn btn-bordered">Каталог</nuxt-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import BrandLogo from '~/components/widgets/brand-logo.vue';
</script>
