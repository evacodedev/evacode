<template>
  <div class="evacode-slide slide-2">
    <img class="slide-main-image" src="/images/new_evacode/Slides/slide_2.jpg" alt="">
    <div class="row">
      <div class="col">
        <div class="slider-container">
          <WidgetsBrandLogo :logo_type="'white'" />
          <h2 class="slider-heading-2">Корейская косметика красота, доступная каждому</h2>
          <nuxt-link :to="{ path: '/collection/leftsidebar/0' }" class="evacode-btn slider-btn">Каталог</nuxt-link>
        </div>
      </div>
    </div>
    <div class="container">
      <div class="row">
        <div class="col">
          <div class="slider-container">
            <h1 class="slider-headline">Корейская косметика красота, доступная каждому</h1>
            <nuxt-link :to="{ path: '/collection/leftsidebar/0' }" class="evacode-btn slider-btn btn-bordered">Каталог</nuxt-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
