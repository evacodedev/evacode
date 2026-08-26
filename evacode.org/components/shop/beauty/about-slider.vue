<template>
    <div>
        <section class="about-slider">
            <div class="container">
                <swiper
                    :loop="true"
                    :slidesPerView="1"
                    :breakpoints="{
                      '640': {
                        slidesPerView: 3,
                        spaceBetween: 50,
                      },
                    }"
                    :navigation="false"
                    :pagination="pagination"
                    :modules="modules"
                    class="swiper-wrapper"
                >
                    <swiper-slide class="swiper-slide">
                        <ShopBeautyAboutSlide1/>
                    </swiper-slide>
                    <swiper-slide class="swiper-slide">
                        <ShopBeautyAboutSlide2/>
                    </swiper-slide>
                    <swiper-slide class="swiper-slide">
                        <ShopBeautyAboutSlide3/>
                    </swiper-slide>
                </swiper>
            </div>
        </section>
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
const pagination = {
    clickable: true,
    renderBullet: function (index, className) {
        return '<span class="' + className + ' evacode-slide-pagination"></span>';
    },
};

const slides = computed(() => slidesResponse.value?.results);

</script>
