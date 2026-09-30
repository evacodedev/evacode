<template>
    <Header/>
    <main class="shared-cart">
        <div class="container">
            <h1 class="shared-cart__title">Корзина по ссылке</h1>

            <div v-if="loading" class="shared-cart__list" aria-hidden="true">
                <div v-for="n in skeletonCount" :key="n" class="shared-cart__item shared-cart__item--skeleton">
                    <div class="skeleton-block shared-cart__image"></div>
                    <div class="product-skeleton shared-cart__info">
                        <div class="skeleton-line short"></div>
                        <div class="skeleton-line"></div>
                    </div>
                </div>
            </div>

            <div v-else-if="!requested.length" class="shared-cart__empty">
                <p>Ссылка не распознана — попросите отправить её ещё раз.</p>
                <nuxt-link to="/collection/leftsidebar/0" class="evacode-btn">В каталог</nuxt-link>
            </div>

            <div v-else-if="loadError" class="shared-cart__empty">
                <p>{{ loadError }}</p>
                <button type="button" class="evacode-btn" @click="load">Повторить</button>
            </div>

            <template v-else>
                <p class="shared-cart__lead">
                    Эту подборку собрали для Вас. Цены и наличие — на сегодня.
                </p>

                <div class="shared-cart__list">
                    <div v-for="item in rows" :key="item.id" class="shared-cart__item">
                        <nuxt-link :to="`/product/${item.id}`" class="shared-cart__image">
                            <img
                                v-if="item.image"
                                :src="catalogImageUrl(item.image, { width: 160, height: 160 })"
                                :alt="item.title"
                                width="160"
                                height="160"
                                loading="lazy"
                            >
                        </nuxt-link>
                        <div class="shared-cart__info">
                            <div v-if="item.brand" class="shared-cart__brand">{{ item.brand }}</div>
                            <nuxt-link :to="`/product/${item.id}`" class="shared-cart__name">{{ item.title }}</nuxt-link>
                            <div v-if="item.clamped" class="shared-cart__note">
                                В наличии только {{ item.quantity }} шт.
                            </div>
                        </div>
                        <div class="shared-cart__qty">{{ item.quantity }} шт.</div>
                        <div class="shared-cart__sum">{{ getPrice(item.retail_price * item.quantity) }}</div>
                    </div>
                </div>

                <p v-if="missingCount" class="shared-cart__note shared-cart__note--block">
                    {{ missingText }}
                </p>

                <template v-if="rows.length">
                    <WidgetsCartShipping
                        class="shared-cart__shipping"
                        :items="rows"
                        :goods-total="total"
                        :country="country"
                        @update:country="country = $event"
                    />

                    <div class="shared-cart__actions">
                        <template v-if="currentCart.length">
                            <button type="button" class="evacode-btn fill-btn" :disabled="!cartReady" @click="apply('replace')">
                                Заменить мою корзину
                            </button>
                            <button type="button" class="evacode-btn" :disabled="!cartReady" @click="apply('merge')">
                                Добавить к моей корзине
                            </button>
                        </template>
                        <button v-else type="button" class="evacode-btn fill-btn" :disabled="!cartReady" @click="apply('replace')">
                            Положить в корзину
                        </button>
                    </div>
                    <p v-if="currentCart.length" class="shared-cart__hint">
                        В Вашей корзине уже есть товары ({{ currentCart.length }}).
                    </p>
                </template>
                <div v-else class="shared-cart__empty">
                    <nuxt-link to="/collection/leftsidebar/0" class="evacode-btn">В каталог</nuxt-link>
                </div>
            </template>
        </div>
    </main>
    <Footer/>
</template>

<script setup>
import { useCartStore } from '~~/store/cart'
import { useProductStore } from '~~/store/products'

useNoIndex()
useHead({ title: 'Корзина по ссылке — Evacode' })

const route = useRoute()
const router = useRouter()
const cartStore = useCartStore()
const productStore = useProductStore()
const apiBase = useRuntimeConfig().public.apiBase

const { country: savedCountry, load: loadSavedCountry, setCountry } = useShippingCountry()

const requested = computed(() => parseSharedCart(route.query.items))
const country = ref(normalizeCountryCode(route.query.country))
const skeletonCount = computed(() => Math.min(Math.max(requested.value.length, 1), 4))

const loading = ref(true)
const loadError = ref('')
const goods = ref([])
const cartReady = ref(false)

const currentCart = computed(() => cartStore.cartItems)

const rows = computed(() => {
    const byId = new Map(goods.value.map((product) => [product.id, product]))
    return requested.value
        .filter(({ id }) => byId.has(id))
        .map(({ id, quantity }) => {
            const product = byId.get(id)
            const stock = Number(product.stock) || 0
            return {
                ...product,
                quantity: Math.min(quantity, stock),
                clamped: quantity > stock,
                image: product.images?.[0]?.url || '',
                brand: product.content_brand?.name || '',
            }
        })
        .filter((item) => item.quantity > 0)
})

const missingCount = computed(() => requested.value.length - rows.value.length)
const missingText = computed(() => {
    if (!rows.value.length) {
        return 'Этих товаров сейчас нет в наличии.'
    }
    return missingCount.value === 1
        ? 'Один товар из подборки сейчас не в наличии — он не попадёт в корзину.'
        : `Товаров не в наличии: ${missingCount.value} — они не попадут в корзину.`
})

const total = computed(() => rows.value.reduce((sum, item) => sum + item.retail_price * item.quantity, 0))

function getPrice(price) {
    return productStore.getPrice(price)
}

async function load() {
    loadError.value = ''
    if (!requested.value.length) {
        loading.value = false
        return
    }
    loading.value = true
    try {
        const ids = requested.value.map(({ id }) => id).join(',')
        const data = await $fetch(`${apiBase}/market/goods/`, {
            query: { ids, page_size: SHARED_CART_MAX_ITEMS },
        })
        goods.value = data?.results || []
    } catch (error) {
        loadError.value = 'Не удалось загрузить товары. Проверьте соединение и попробуйте ещё раз.'
    } finally {
        loading.value = false
    }
}

async function ensureLocalCart() {
    if (cartStore.cart.length) {
        return
    }
    try {
        const stored = JSON.parse((await useLocalForage().getItem('evacode_cart')) || '[]')
        if (stored?.length && !cartStore.cart.length) {
            cartStore.setInitialCart(stored)
        }
    } catch (error) {
        return
    }
}

function apply(mode) {
    if (country.value) {
        setCountry(country.value)
    }
    const items = rows.value.map(({ clamped, image, brand, ...product }) => product)
    if (mode === 'replace') {
        cartStore.setInitialCart(items)
    } else {
        const merged = cartStore.cart.map((item) => ({ ...item }))
        for (const product of items) {
            const existing = merged.find((item) => item.id === product.id)
            if (existing) {
                existing.quantity = Math.min(existing.quantity + product.quantity, Number(product.stock) || existing.quantity)
            } else {
                merged.push(product)
            }
        }
        cartStore.setInitialCart(merged)
    }
    router.push('/page/account/cart')
}

onMounted(async () => {
    if (!country.value) {
        loadSavedCountry()
        country.value = savedCountry.value
    }
    await Promise.all([load(), ensureLocalCart()])
    cartReady.value = true
})
</script>
