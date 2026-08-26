<template>
  <div>
    <section class="p-0">
      <div class="slide-1 home-slider">

        <swiper
            :loop="true"
            :navigation="false"
            :pagination="pagination"
            :modules="modules"
            class="swiper-wrapper"
        >
          <swiper-slide class="swiper-slide">
            <ShopBeautySlidesSlide1 />
          </swiper-slide>

          <swiper-slide class="swiper-slide">
            <ShopBeautySlidesSlide2 />
          </swiper-slide>

          <swiper-slide class="swiper-slide">
            <ShopBeautySlidesSlide3 />
          </swiper-slide>

          <swiper-slide class="swiper-slide">
            <ShopBeautySlidesSlide4 />
          </swiper-slide>

          <swiper-slide class="swiper-slide">
            <ShopBeautySlidesSlide5 />
          </swiper-slide>

          <swiper-slide class="swiper-slide">
            <ShopBeautySlidesSlide6 />
          </swiper-slide>

        </swiper>

      </div>
    </section>
    <!-- Home slider end -->
  </div>
</template>

<script type="text/javascript" setup>
import {Swiper, SwiperSlide} from 'swiper/vue';
import 'swiper/css';
import 'swiper/css/navigation';
import 'swiper/css/pagination';
import {Navigation} from 'swiper';
import {Pagination} from 'swiper';

const modules = [Navigation, Pagination];
const {data: slidesResponse} = await useAsyncData(
    'slidesResponse',
    () => $fetch(`${useRuntimeConfig().public.apiBase}/core/slide`),
    {
      server: false,
    }
);
const pagination = {
  clickable: true,
  renderBullet: function (index, className) {
    return '<span class="' + className + ' evacode-slide-pagination"></span>';
  },
};

const slides = computed(() => slidesResponse.value?.results);

</script>
