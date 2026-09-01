<template>
    <Header/>
    <div v-if="showNotFound" class="product-page-shell">
        <section class="section-b-space product-details-section">
            <div class="container text-center section-t-space section-b-space">
                <img src="/images/evacode/empty-search.jpg" class="img-fluid" alt=""/>
                <h3 class="mt-3">Товар недоступен</h3>
                <p class="mt-2">Возможно, его уже нет в каталоге.</p>
                <nuxt-link to="/collection/leftsidebar/0" class="btn btn-solid mt-3">В каталог</nuxt-link>
            </div>
        </section>
    </div>
    <div v-else-if="!product" class="product-page-shell">
        <section class="section-b-space product-details-section">
            <div class="container">
                <div class="row">
                    <div class="col-lg-3 d-none d-lg-block">
                        <div class="skeleton-block" style="height: 420px"></div>
                    </div>
                    <div class="col-lg-9">
                        <div class="row g-4">
                            <div class="col-lg-6">
                                <div class="skeleton-block" style="aspect-ratio: 1 / 1"></div>
                            </div>
                            <div class="col-lg-6">
                                <div class="product-skeleton">
                                    <div class="skeleton-line"></div>
                                    <div class="skeleton-line short"></div>
                                    <div class="skeleton-line" style="margin-top: 32px; max-width: 55%"></div>
                                    <div class="skeleton-block" style="height: 50px; margin-top: 28px"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </div>
    <div v-else>
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
                                        <Swiper v-if="productImages.length" @swiper="onSwiper" :slidesPerView="1" :spaceBetween="20"
                                                class="swiper-wrapper h-auto">
                                            <SwiperSlide class="swiper-slide" v-for="(image, index) in productImages"
                                                         :key="index">
                                                <img :src="image.url" :id="image.image_id"
                                                     class="img-fluid bg-img"
                                                     :class="{ 'is-loaded': loadedImages[index] }"
                                                     :alt="image.alt || product.title"
                                                     @load="markImageLoaded(index)"/>
                                            </SwiperSlide>
                                        </Swiper>
                                        <div v-else class="skeleton-block" style="aspect-ratio: 1 / 1"></div>
                                        <div class="row" v-if="productImages.length > 1">
                                            <div class="col-12 slider-nav-images">
                                                <Swiper :slidesPerView="3" slide-active-class="true" :spaceBetween="20"
                                                        class="swiper-wrapper">
                                                    <SwiperSlide class="swiper-slide"
                                                                 v-for="(image, index) in productImages" :key="index"
                                                                 :class="slideId == index ? 'product-slider-active' : ''">
                                                        <img :src="image.url" :id="image.image_id"
                                                             class="img-fluid bg-img"
                                                             :alt="image.alt || product.title" @click="slideTo(index)"/>
                                                    </SwiperSlide>
                                                </Swiper>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="col-lg-6 rtl-text">
                                        <div class="product-right">
                                            <h2>{{ product.title }}</h2>
                                            <h4 v-if="product.official_price">
                                                <del>{{ getPrice(product.official_price) }}</del>
                                                <span v-if="discountPercent">{{ discountPercent }}% off</span>
                                            </h4>
                                            <h3 v-if="product.retail_price != null">{{ getPrice(product.retail_price) }}</h3>
                                            <div class="skeleton-line" v-else style="max-width: 40%; margin: 12px 0"></div>
                                            <div class="pro_inventory" v-if="product.stock != null && product.stock < 8">
                                                <p class="active"> Поспешите! У нас осталось всего {{ product.stock }}
                                                    шт. на складе. </p>
                                            </div>
                                            <div class="product-buttons">
                                                <nuxt-link :to="{ path: '/page/account/cart' }">
                                                    <button class="evacode-btn large-btn" title="Добавить в корзину"
                                                            @click="addToCart(product, counter)"
                                                            :disabled="product.stock == null || counter > product.stock">Добавить в корзину
                                                    </button>
                                                </nuxt-link>
                                            </div>
                                            <div class="product-description border-product">
                                                <h5 class="avalibility" v-if="product.stock != null && counter <= product.stock">
                                                    <span>В наличии</span>
                                                </h5>
                                                <h5 class="avalibility" v-if="product.stock != null && counter > product.stock">
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
                                                               :disabled="product.stock != null && counter > product.stock" v-model="counter"/>
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
                                                <div
                                                    v-if="product.description"
                                                    class="product-detail-description"
                                                    v-html="product.description"
                                                ></div>
                                                <div v-else-if="pending" class="product-skeleton">
                                                    <div class="skeleton-line"></div>
                                                    <div class="skeleton-line"></div>
                                                    <div class="skeleton-line short"></div>
                                                </div>
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
const { previewFor } = useProductPreview();
const runtimeConfig = useRuntimeConfig();

const slideId = ref(0);
const counter = ref(1);
const swiper = ref({});
const productId = String(route.params.id);
const isProductRoute = computed(() => String(route.path).includes('/product/sidebar'));

const { data: productResponse, pending, status, error } = await useAsyncData(
    `goods-product-${productId}`,
    () => $fetch(`${runtimeConfig.public.apiBase}/market/goods`, {
        query: { id: productId },
    }),
    {
        lazy: import.meta.client,
    },
);

const fetchedProduct = computed(() => productResponse.value?.results?.[0] ?? null);
const product = computed(() => fetchedProduct.value || previewFor(productId));
const productImages = computed(() => product.value?.images || []);
const showNotFound = computed(() =>
    isProductRoute.value
    && !pending.value
    && !fetchedProduct.value
    && (status.value === 'success' || status.value === 'error' || Boolean(error.value)),
);

const loadedImages = ref({});
const markImageLoaded = (index) => {
    loadedImages.value = { ...loadedImages.value, [index]: true };
};

const onSwiper = (_swiper) => swiper.value = _swiper;

const addToCart = (item, qty) => {
    item.quantity = qty || 1
    useCartStore().addToCart(item)
};

const getPrice = (price) => {
    return useProductStore().getPrice(price);
};

const increment = () => counter.value++;
const decrement = () => {
    if (counter.value > 1) counter.value--
};

const discountPercent = computed(() => {
    const item = product.value;
    if (!item?.official_price) {
        return 0;
    }
    return (((item.official_price - item.retail_price) / item.official_price) * 100).toFixed(0);
});

const slideTo = (id) => {
    swiper.value?.slideTo(id)
    slideId.value = id
};

useHead({
    meta: [
        {name: 'description', content: () => product.value?.title},
        {name: 'og:description', content: () => product.value?.title},
        {name: 'twitter:description', content: () => product.value?.title},
        {name: 'og:title', content: () => product.value?.title}
    ],
    titleTemplate: () => product.value?.title || 'Товар',
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
