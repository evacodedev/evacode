<template>
    <div>
        <section class="testimonials">
            <div class="container">
                <swiper
                    :loop="true"
                    :slidesPerView="1"
                    :breakpoints="{
                      '640': {
                        slidesPerView: 1,
                      },
                      '1024': {
                        slidesPerView: 2,
                        spaceBetween: 30,
                      },
                      '1200': {
                        slidesPerView: 3,
                        spaceBetween: 50,
                      },
                    }"
                    :navigation="false"
                    :pagination="pagination"
                    :modules="modules"
                    class="swiper-wrapper"
                >

                    <SwiperSlide class="swiper-slide" v-for="(testimonial, index) in testimonials"
                                 :key="index">
                        <ShopBeautyTestimonialsTestimonialSlide :testimonial="testimonial" />
                    </SwiperSlide>
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
import {useTestimonialsStore} from '~/store/testimonials';

const modules = [Navigation, Pagination];
const pagination = {
    clickable: true,
    renderBullet: function (index, className) {
        return '<span class="' + className + ' evacode-slide-pagination"></span>';
    },
};

const testimonials = await useTestimonialsStore().testimonials;
</script>
