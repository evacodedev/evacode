<template>
    <Header/>
    <div v-if="!!product">
        <section class="section-b-space product-details-section">
            <div class="collection-wrapper">
                <div class="container">
                    <div class="row">
                        <div class="col-lg-3">
                            <WidgetsCollectionSidebar/>
                        </div>
                        <div class="col-lg-9 col-sm-12 col-xs-12 productdetail">
                            <div class="container-fluid">
                                <div class="row">
                                    <div class="col-lg-6">
                                        <Swiper @swiper="onSwiper" :slidesPerView="1" :spaceBetween="20"
                                                class="swiper-wrapper h-auto">
                                            <SwiperSlide class="swiper-slide" v-for="(image, index) in product.images"
                                                         :key="index">
                                                <img :src="image.url" :id="image.image_id" class="img-fluid bg-img"
                                                     :alt="image.alt"/>
                                            </SwiperSlide>
                                        </Swiper>
                                        <div class="row">
                                            <div class="col-12 slider-nav-images">
                                                <Swiper :slidesPerView="3" slide-active-class="true" :spaceBetween="20"
                                                        class="swiper-wrapper">
                                                    <SwiperSlide class="swiper-slide"
                                                                 v-for="(image, index) in product.images" :key="index"
                                                                 :class="slideId == index ? 'product-slider-active' : ''">
                                                        <img :src="image.url" :id="image.image_id"
                                                             class="img-fluid bg-img"
                                                             alt="image.alt" @click="slideTo(index)"/>
                                                    </SwiperSlide>
                                                </Swiper>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-lg-6 rtl-text">
                                        <div class="product-right">
                                            <h2>{{ product.title }}</h2>
                                            <h4>
                                                <del>{{ getPrice(product.official_price) }}</del>
                                                <span>{{ getDiscountPercentages(product) }}% off</span>
                                            </h4>
                                            <h3>{{ getPrice(product.retail_price) }}</h3>
                                            <div class="pro_inventory" v-if="product.stock < 8">
                                                <p class="active"> Поспешите! У нас осталось всего {{ product.stock }}
                                                    шт. на складе. </p>
                                            </div>
                                            <div class="product-buttons">
                                                <nuxt-link :to="{ path: '/page/account/cart' }">
                                                    <button class="evacode-btn large-btn" title="Добавить в корзину"
                                                            @click="addToCart(product, counter)"
                                                            :disabled="counter > product.stock">Добавить в корзину
                                                    </button>
                                                </nuxt-link>
                                            </div>
                                            <div class="product-description border-product">
                                                <h5 class="avalibility" v-if="counter <= product.stock">
                                                    <span>В наличии</span>
                                                </h5>
                                                <h5 class="avalibility" v-if="counter > product.stock">
                                                    <span>Отсутствует</span>
                                                </h5>
                                                <h6 class="product-title">количество</h6>
                                                <div class="qty-box">
                                                    <div class="input-group">
                            <span class="input-group-prepend">
                              <button type="button" class="btn quantity-left-minus" data-type="minus" data-field
                                      @click="decrement()">
                                <i class="ti-angle-left"></i>
                              </button>
                            </span>
                                                        <input type="text" name="quantity"
                                                               class="form-control input-number"
                                                               :disabled="counter > product.stock" v-model="counter"/>
                                                        <span class="input-group-prepend">
                              <button type="button" class="btn quantity-right-plus" data-type="plus" data-field
                                      @click="increment()">
                                <i class="ti-angle-right"></i>
                              </button>
                            </span>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="border-product">
                                                <h6 class="product-title">Описание товара</h6>
                                                <div class="product-detail-description"
                                                     v-html="product.description"></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <ShopBeautyAboutCons/>
                        </div>
                    </div>
                </div>
            </div>
            <!--      <WidgetsRelatedProducts :productTYpe="productTYpe" :productId="productId"/>-->
            <div class="modal fade " id="modal-1" aria-hidden="true" tabindex="-1" role="dialog"
                 aria-labelledby="modal-cartLabel">
                <div class="modal-dialog modal-md modal-dialog-centered">
                    <div class="modal-content">
                        <div class="row">
                            <div class="col-lg-12">
                                <div class="modal-header"><h5 class="modal-title">{{ product.title }}</h5>
                                    <button type="button" class="btn-close" aria-label="Close"
                                            data-bs-dismiss="modal"></button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </div>
    <ShopBeautyTestimonials/>
    <ShopBeautyAboutSlider/>

    <Footer/>
</template>

<script setup>

import {Swiper, SwiperSlide} from 'swiper/vue';
import 'swiper/css';
import {useProductStore} from '~~/store/products';
import {useCartStore} from '~~/store/cart';
import {useRoute} from 'vue-router';
import {Navigation, Pagination} from 'swiper';

const route = useRoute();

const slideId = ref(0);
const counter = ref(1);
const swiper = ref({});

const product = computed(() => productResponse.value?.results[0]);

const {data: productResponse} = await useAsyncData(
    'productResponse',
    () => $fetch(`${useRuntimeConfig().public.apiBase}/market/goods`, {
        query: {
            id: route.params.id,
        }
    }),
    {
        server: false,
    }
);

const onSwiper = (_swiper) => swiper.value = _swiper;

// add to cart
const addToCart = (product, qty) => {
    product.quantity = qty || 1
    useCartStore().addToCart(product)
};

const getPrice = (price) => {
    return useProductStore().getPrice(price);
};

// Item Count
const increment = () => counter.value++;
const decrement = () => {
    if (counter.value > 1) counter.value--
};

const getDiscountPercentages = (product) => {
    return (((product.official_price - product.retail_price) / product.official_price) * 100).toFixed(0);
};

const slideTo = (id) => {
    swiper.value.slideTo(id)

    slideId.value = id
};

useHead({
    meta: [
        {name: 'description', content: product.value?.title},
        {name: 'og:description', content: product.value?.title},
        {name: 'twitter:description', content: product.value?.title},
        {name: 'og:title', content: product.value?.title}
    ],
    titleTemplate: product.value?.title,
});


const modules = [Navigation, Pagination];
const pagination = {
    clickable: true,
    renderBullet: function (index, className) {
        return '<span class="' + className + ' evacode-slide-pagination"></span>';
    },
};

</script>

<style scoped>
.swiper-slide .img-fluid {
    object-fit: cover;
    object-position: center;
    aspect-ratio: 1 / 1;
}
</style>
