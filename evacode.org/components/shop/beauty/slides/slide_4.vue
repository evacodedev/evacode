<template>
  <div class="evacode-slide slide-4">
    <img class="slide-main-image" src="/images/new_evacode/Slides/slide_4.jpg" alt="">
    <div class="row">
      <div class="col">
        <div class="slider-container">
          <WidgetsBrandLogo />
          <h2 class="slider-heading-2">Акция</h2>
          <p class="slider-description">В честь дня рождения ЕваКод <br/> дарим скидку!  <br/>Вся косметика по оптовой цене</p>
          <nuxt-link :to="{ path: '/collection/leftsidebar/0' }" class="evacode-btn slider-btn">Купить</nuxt-link>
        </div>
      </div>
    </div>
    <div class="container">
      <div class="row">
        <div class="col">
          <div class="slider-container">
            <h1 class="slider-headline">Акция</h1>
            <p class="slider-description">В честь дня рождения ЕваКод дарим скидку! Вся косметика по оптовой цене</p>
            <nuxt-link :to="{ path: '/collection/leftsidebar/0' }" class="evacode-btn slider-btn btn-bordered">Купить</nuxt-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
</script>
