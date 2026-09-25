<template>
  <div class="evacode-slide slide-3">
    <img
      class="slide-main-image"
      src="/images/new_evacode/Slides/slide_3.webp"
      alt="Оригинальная корейская косметика от профессионалов"
      width="1920"
      height="600"
      loading="lazy"
    >
    <div class="row">
      <div class="col">
        <div class="slider-container">
          <WidgetsBrandLogo :logo_type="'white'" />
          <h2 class="slider-heading-2">Доверьте свою красоту профессионалам!</h2>
          <p class="slider-description-white">Мы гарантируем оригинальность <br/>каждого продукта</p>
          <nuxt-link :to="{ path: '/collection/leftsidebar/0' }" class="evacode-btn slider-btn">Каталог</nuxt-link>
        </div>
      </div>
    </div>
    <div class="container">
      <div class="row">
        <div class="col">
          <div class="slider-container">
            <p class="slider-headline">Доверьте свою красоту профессионалам!</p>
            <p class="slider-description">Мы гарантируем оригинальность каждого продукта</p>
            <nuxt-link :to="{ path: '/collection/leftsidebar/0' }" class="evacode-btn slider-btn btn-bordered">Каталог</nuxt-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
</script>
