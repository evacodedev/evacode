<template>
  <div class="evacode-slide slide-3">
    <img class="slide-main-image" src="/images/new_evacode/Slides/slide_3.jpg" alt="">
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
            <h1 class="slider-headline">Доверьте свою красоту профессионалам!</h1>
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
