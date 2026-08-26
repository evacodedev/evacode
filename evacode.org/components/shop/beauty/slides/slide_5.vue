<template>
  <div class="evacode-slide slide-5">
    <img class="slide-main-image" src="/images/new_evacode/Slides/slide_5.jpg" alt="">
    <div class="row">
      <div class="col">
        <div class="slider-container">
          <WidgetsBrandLogo :logo_type="'white'" />
          <h2 class="slider-heading-2">Опт и розница</h2>
          <p class="slider-description-white">эксклюзивная корейская косметика с выгодой до 60%!</p>
          <nuxt-link :to="{ path: '/collection/leftsidebar/0' }" class="evacode-btn slider-btn">Купить</nuxt-link>
        </div>
      </div>
    </div>
    <div class="container">
      <div class="row">
        <div class="col">
          <div class="slider-container">
            <h1 class="slider-headline">Опт и розница</h1>
            <p class="slider-description">эксклюзивная корейская косметика с выгодой до 60%!</p>
            <nuxt-link :to="{ path: '/collection/leftsidebar/0' }" class="evacode-btn slider-btn btn-bordered">Купить</nuxt-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
