<template>
  <div class="evacode-slide slide-1">
    <img class="slide-main-image" src="/images/new_evacode/Slides/slide_1.jpg" alt="">
    <div class="row">
      <div class="col">
        <div class="slider-container">
          <WidgetsBrandLogo />
          <h1 class="slider-headline">Премиальное качество!</h1>
          <p class="slider-description">люксовая косметика от ведущих корейских производителей</p>
          <nuxt-link :to="{ path: '/collection/leftsidebar/0' }" class="evacode-btn slider-btn">Каталог</nuxt-link>
        </div>
      </div>
    </div>
    <div class="container">
      <div class="row">
        <div class="col">
          <div class="slider-container">
            <h1 class="slider-headline">Премиальное качество!</h1>
            <p class="slider-description">люксовая косметика от ведущих корейских производителей</p>
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
