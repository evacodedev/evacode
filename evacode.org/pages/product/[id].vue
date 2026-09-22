<template>
    <Header/>
    <div v-if="showNotFound" class="product-pdp">
        <div class="container">
            <nav class="product-pdp__nav">
                <nuxt-link :to="lastCatalogPath" class="product-pdp__back">
                    <i class="fa fa-angle-left" aria-hidden="true"></i>
                    Назад к списку
                </nuxt-link>
            </nav>
            <div class="product-pdp__empty">
            <h1>Товар недоступен</h1>
            <p>Возможно, его уже нет в каталоге.</p>
            <nuxt-link to="/collection/leftsidebar/0" class="btn btn-solid">В каталог</nuxt-link>
            </div>
        </div>
    </div>
    <div v-else-if="!product" class="product-pdp">
        <div class="container">
            <nav class="product-pdp__nav">
                <nuxt-link :to="lastCatalogPath" class="product-pdp__back">
                    <i class="fa fa-angle-left" aria-hidden="true"></i>
                    Назад к списку
                </nuxt-link>
            </nav>
            <div class="product-pdp__layout">
            <div class="product-pdp__gallery">
                <div class="skeleton-block product-pdp__hero-skel"></div>
            </div>
            <div class="product-pdp__buy">
                <div class="product-skeleton">
                    <div class="skeleton-line short"></div>
                    <div class="skeleton-line"></div>
                    <div class="skeleton-line short"></div>
                    <div class="skeleton-block" style="height: 48px; margin-top: 28px"></div>
                </div>
            </div>
        </div>
        </div>
    </div>
    <div v-else class="product-pdp" :class="{ 'is-ready': motionReady }">
        <div class="container">
            <nav class="product-pdp__nav">
                <nuxt-link :to="lastCatalogPath" class="product-pdp__back">
                    <i class="fa fa-angle-left" aria-hidden="true"></i>
                    Назад к списку
                </nuxt-link>
            </nav>
            <div class="product-pdp__layout">
            <div class="product-pdp__gallery motion-appear" style="--i: 0">
                <div v-if="productImages.length > 1" class="product-pdp__thumbs">
                    <button
                        v-for="(image, index) in productImages"
                        :key="'t-' + (image.id || index)"
                        type="button"
                        class="product-pdp__thumb"
                        :class="{ 'is-active': slideId === index }"
                        @click="slideTo(index)"
                    >
                        <img :src="image.url" :alt="product.title"/>
                    </button>
                </div>
                <div class="product-pdp__stage">
                    <Swiper
                        v-if="productImages.length"
                        @swiper="onSwiper"
                        :slidesPerView="1"
                        :spaceBetween="0"
                        class="product-pdp__hero"
                    >
                        <SwiperSlide v-for="(image, index) in productImages" :key="image.id || index">
                            <img
                                :src="image.url"
                                class="product-pdp__photo"
                                :class="{ 'is-loaded': loadedImages[index] }"
                                :alt="product.title"
                                @load="markImageLoaded(index)"
                                @error="markImageLoaded(index)"
                            />
                        </SwiperSlide>
                    </Swiper>
                    <div v-else class="skeleton-block product-pdp__hero-skel"></div>
                </div>
            </div>
            <div class="product-pdp__buy motion-appear" style="--i: 2">
                <p v-if="brandName" class="product-pdp__brand">
                    <nuxt-link
                        v-if="brandPageHref"
                        :to="brandPageHref"
                        class="product-pdp__brand-link"
                    >{{ brandName }}</nuxt-link>
                    <template v-else>{{ brandName }}</template>
                </p>
                <h1 class="product-pdp__title">{{ product.title }}</h1>
                <p v-if="metaLine" class="product-pdp__meta">{{ metaLine }}</p>
                <div class="product-pdp__price">
                    <span v-if="product.official_price" class="product-pdp__was">{{ getPrice(product.official_price) }}</span>
                    <strong v-if="product.retail_price != null">{{ getPrice(product.retail_price) }}</strong>
                    <span v-if="discountPercent" class="product-pdp__off">−{{ discountPercent }}%</span>
                </div>
                <p v-if="product.stock != null && product.stock < 8" class="product-pdp__stock">
                    Осталось {{ product.stock }} шт.
                </p>
                <div class="product-pdp__qty">
                    <span>Количество</span>
                    <div class="product-pdp__qty-box">
                        <button type="button" @click="decrement" aria-label="Меньше">−</button>
                        <input v-model="counter" type="text" name="quantity" :disabled="outOfStock"/>
                        <button type="button" @click="increment" aria-label="Больше">+</button>
                    </div>
                </div>
                <button
                    class="product-pdp__cta"
                    type="button"
                    :disabled="outOfStock || product.stock == null || counter > product.stock"
                    @click="addToCart(product, counter)"
                >
                    Добавить в корзину
                </button>
                <p class="product-pdp__avail">{{ outOfStock ? 'Нет в наличии' : 'В наличии' }}</p>
                <p
                    class="product-pdp__notice"
                    :class="{ 'is-on': addedNotice }"
                    role="status"
                    aria-live="polite"
                >
                    <span v-if="addedNotice">Добавлено в корзину</span>
                </p>
                <nuxt-link
                    to="/page/account/cart/"
                    class="product-pdp__checkout"
                    :class="{ 'is-disabled': !cartHasItems }"
                    :aria-disabled="!cartHasItems"
                    :tabindex="cartHasItems ? 0 : -1"
                    @click="onCheckoutClick"
                >
                    Оформить заказ
                </nuxt-link>
                <div class="product-pdp__help">
                    <p class="product-pdp__note">
                        <i class="fa fa-exclamation-circle" aria-hidden="true"></i>
                        <span>К цене товара может добавиться стоимость доставки.</span>
                    </p>
                    <div class="product-pdp__help-acc" :class="{ 'is-open': contactsOpen }">
                        <button
                            type="button"
                            class="product-pdp__help-head"
                            :aria-expanded="contactsOpen"
                            aria-controls="pdp-contacts"
                            @click="contactsOpen = !contactsOpen"
                        >
                            <span>Контакты для связи</span>
                            <span class="product-pdp__acc-icon" aria-hidden="true"></span>
                        </button>
                        <div
                            id="pdp-contacts"
                            class="product-pdp__help-panel"
                            :class="{ 'is-open': contactsOpen }"
                            :inert="!contactsOpen"
                        >
                            <div class="product-pdp__help-inner">
                                <WidgetsMessengerLinks
                                    variant="pdp"
                                    phone="+8210-7652-8595"
                                    phone-href="tel:+821076528595"
                                    email="sales@evacode.org"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div v-if="accordionItems.length" class="product-pdp__accordion motion-appear" style="--i: 5">
                <div
                    v-for="item in accordionItems"
                    :key="item.kind"
                    class="product-pdp__acc"
                    :class="{ 'is-open': isAccordionOpen(item.kind) }"
                >
                    <button
                        type="button"
                        class="product-pdp__acc-head"
                        :aria-expanded="isAccordionOpen(item.kind)"
                        :aria-controls="'pdp-acc-' + item.kind"
                        @click="toggleAccordion(item.kind)"
                    >
                        <span class="product-pdp__acc-title">{{ item.heading }}</span>
                        <span class="product-pdp__acc-icon" aria-hidden="true"></span>
                    </button>
                    <div
                        :id="'pdp-acc-' + item.kind"
                        class="product-pdp__acc-panel"
                        :class="{ 'is-open': isAccordionOpen(item.kind) }"
                        :inert="!isAccordionOpen(item.kind)"
                    >
                        <div class="product-pdp__acc-inner">
                        <p
                            v-for="(para, paraIndex) in bodyParagraphs(item)"
                            :key="item.kind + '-p-' + paraIndex"
                            class="product-pdp__body"
                        >{{ para }}</p>
                        <ul v-if="isStringList(item)" class="product-pdp__list">
                            <li v-for="(row, i) in stringListItems(item)" :key="i">{{ row }}</li>
                        </ul>
                        <dl v-else-if="isNamedList(item)" class="product-pdp__ingredients">
                            <div v-for="(row, i) in item.items" :key="i">
                                <dt>{{ row.name }}</dt>
                                <dd>{{ row.text }}</dd>
                            </div>
                        </dl>
                        <div
                            v-if="item.html"
                            class="product-pdp__html is-open"
                            v-html="item.html"
                        ></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        </div>
        <div v-if="product" class="product-pdp__sticky">
            <div class="container product-pdp__sticky-bar">
                <span>{{ getPrice(product.retail_price) }}</span>
                <button
                    type="button"
                    :disabled="outOfStock || product.stock == null || counter > product.stock"
                    @click="addToCart(product, counter)"
                >
                    В корзину
                </button>
            </div>
        </div>
    </div>
    <Footer/>
</template>

<script setup>
import { Swiper, SwiperSlide } from 'swiper/vue';
import 'swiper/css';
import { useProductStore } from '~~/store/products';
import { useCartStore } from '~~/store/cart';
import { useRoute } from 'vue-router';

const FALLBACK_HEADINGS = {
    description: 'Описание',
    about: 'О товаре',
    benefits: 'Преимущества',
    ingredients: 'Основные компоненты',
    texture: 'Текстура и финиш',
    how_to_use: 'Способ применения',
    suitable_for: 'Подходит для',
    volume: 'Объём',
    weight: 'Вес',
    set_contents: 'Состав набора',
    rest: '',
};

const route = useRoute();
const { previewFor } = useProductPreview();
const { lastCatalogPath } = useCatalogReturn();
const runtimeConfig = useRuntimeConfig();

const slideId = ref(0);
const counter = ref(1);
const swiper = ref({});
const openKinds = ref({ description: true });
const motionReady = ref(false);
const addedNotice = ref(false);
const contactsOpen = ref(false);
let addedNoticeTimer;
const productId = String(route.params.id);
const cartStore = useCartStore();
const cartHasItems = computed(() => cartStore.cart.length > 0);

const { data: productResponse, pending, status, error } = await useAsyncData(
    `goods-pdp-${productId}`,
    () => $fetch(`${runtimeConfig.public.apiBase}/market/goods/${productId}/`),
    {
        lazy: import.meta.client,
    },
);

const fetchedProduct = computed(() => {
    const payload = productResponse.value;
    if (!payload || payload.id == null) {
        return null;
    }
    return payload;
});
const product = computed(() => fetchedProduct.value || previewFor(productId));
const productImages = computed(() => product.value?.images || []);
const showNotFound = computed(() =>
    !pending.value
    && !fetchedProduct.value
    && (status.value === 'success' || status.value === 'error' || Boolean(error.value)),
);
const outOfStock = computed(() => product.value?.stock != null && counter.value > product.value.stock);
const contentBlocks = computed(() => product.value?.content_blocks || []);
const brandName = computed(() => product.value?.content_brand?.name || '');
const brandPageHref = computed(() => {
    const brand = product.value?.content_brand;
    if (!brand?.page || !brand.slug) {
        return '';
    }
    return `/brand/${brand.slug}`;
});
const volumeText = computed(() => contentBlocks.value.find((block) => block.kind === 'volume')?.body || '');
const kindName = computed(() => product.value?.content_kind?.name || '');
const metaLine = computed(() => [kindName.value, volumeText.value].filter(Boolean).join(' · '));
const blockHeading = (block) => block.heading || FALLBACK_HEADINGS[block.kind] || '';
const accordionItems = computed(() => {
    const blocks = contentBlocks.value.filter((block) => {
        if (block.kind === 'volume' || block.kind === 'weight') {
            return false;
        }
        return Boolean(block.body || (block.items && block.items.length));
    });
    const items = [];
    const seen = new Set();
    const pushBlock = (block, kind, heading) => {
        if (!block || seen.has(kind)) {
            return;
        }
        const hasText = Boolean(block.body || (block.items && block.items.length) || block.html);
        if (!hasText) {
            return;
        }
        seen.add(kind);
        items.push({ ...block, kind, heading });
    };
    const lead = blocks.find((block) => block.kind === 'lead');
    const about = blocks.find((block) => block.kind === 'about');
    pushBlock(lead, 'description', 'Описание');
    if (about && about.body && lead?.body && about.body.trim() === lead.body.trim()) {
        // skip duplicate about
    } else {
        pushBlock(about, 'about', blockHeading(about || { kind: 'about', heading: '' }));
    }
    blocks
        .filter((block) => block.kind !== 'lead' && block.kind !== 'about')
        .forEach((block) => {
            const heading = blockHeading(block);
            if (heading) {
                pushBlock(block, block.kind, heading);
            }
        });
    if (!items.length && product.value?.description) {
        return [{ kind: 'description', heading: 'Описание', html: product.value.description, items: [] }];
    }
    return items;
});
const discountPercent = computed(() => {
    const item = product.value;
    if (!item?.official_price || item.retail_price == null) {
        return 0;
    }
    return Math.round(((item.official_price - item.retail_price) / item.official_price) * 100);
});
const isAccordionOpen = (kind) => Boolean(openKinds.value[kind]);
const toggleAccordion = (kind) => {
    openKinds.value = {
        ...openKinds.value,
        [kind]: !openKinds.value[kind],
    };
};
const isStringList = (block) =>
    Array.isArray(block.items)
    && block.items.length
    && typeof block.items[0] === 'string';
const stringListItems = (block) => {
    if (!isStringList(block)) {
        return [];
    }
    return block.items.flatMap((row) =>
        String(row)
            .split(/\s*[•●▪◦]\s*/)
            .map((part) => part.trim())
            .filter(Boolean),
    );
};
const isNamedList = (block) =>
    Array.isArray(block.items)
    && block.items.length
    && typeof block.items[0] === 'object';
const bodyParagraphs = (block) =>
    String(block?.body || '')
        .split(/\n\s*\n/)
        .map((para) => para.trim())
        .filter(Boolean);

const loadedImages = ref({});
const markImageLoaded = (index) => {
    loadedImages.value = { ...loadedImages.value, [index]: true };
};
const onSwiper = (_swiper) => {
    swiper.value = _swiper;
};

onMounted(() => {
    requestAnimationFrame(() => {
        motionReady.value = true;
    });
});

onBeforeUnmount(() => {
    if (addedNoticeTimer) {
        clearTimeout(addedNoticeTimer);
    }
});

const showAddedNotice = () => {
    addedNotice.value = true;
    if (addedNoticeTimer) {
        clearTimeout(addedNoticeTimer);
    }
    addedNoticeTimer = setTimeout(() => {
        addedNotice.value = false;
    }, 4000);
};

const addToCart = (item, qty) => {
    const payload = {
        id: item.id,
        title: item.title,
        official_price: item.official_price,
        retail_price: item.retail_price,
        stock: item.stock,
        images: item.images,
        quantity: qty || 1,
    };
    cartStore.addToCart(payload);
    showAddedNotice();
};

const onCheckoutClick = (event) => {
    if (!cartHasItems.value) {
        event.preventDefault();
    }
};

const getPrice = (price) => useProductStore().getPrice(price);

const increment = () => {
    counter.value++;
};
const decrement = () => {
    if (counter.value > 1) {
        counter.value--;
    }
};

const slideTo = (id) => {
    swiper.value?.slideTo(id);
    slideId.value = id;
};

const stripHtml = (value) => String(value || '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const seoDescription = computed(() => {
    const lead = contentBlocks.value.find((block) => block.kind === 'lead')?.body;
    const text = stripHtml(lead || product.value?.description || '');
    const fallback = [brandName.value, product.value?.title, 'купить в EvaCode']
        .filter(Boolean)
        .join('. ');
    const raw = text || fallback;
    if (raw.length <= 180) {
        return raw;
    }
    return `${raw.slice(0, 177)}…`;
});

useHead({
    title: () => (product.value?.title ? `${product.value.title} — EvaCode` : 'Товар — EvaCode'),
    meta: [
        { name: 'description', content: () => seoDescription.value },
        { property: 'og:title', content: () => product.value?.title || 'EvaCode' },
        { property: 'og:description', content: () => seoDescription.value },
    ],
    script: () => {
        if (!product.value) {
            return [];
        }
        const site = String(runtimeConfig.public.url || 'https://www.evacode.org').replace(/\/$/, '');
        const image = product.value.images?.[0]?.url;
        return [
            {
                type: 'application/ld+json',
                innerHTML: JSON.stringify({
                    '@context': 'https://schema.org',
                    '@type': 'Product',
                    name: product.value.title,
                    description: seoDescription.value,
                    image: image || undefined,
                    brand: brandName.value
                        ? { '@type': 'Brand', name: brandName.value }
                        : undefined,
                    url: `${site}/product/${product.value.id}/`,
                    offers: {
                        '@type': 'Offer',
                        url: `${site}/product/${product.value.id}/`,
                        availability: outOfStock.value
                            ? 'https://schema.org/OutOfStock'
                            : 'https://schema.org/InStock',
                    },
                }),
            },
        ];
    },
});
</script>
