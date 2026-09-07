<template>
<NuxtLayout >
    <Head></Head>
    <NuxtLoadingIndicator :height="2" :duration="2000" :throttle="200" color="#B89254" />
    <NuxtPage :page-key="(route) => route.path" />
    <WidgetsCartDrawer />
</NuxtLayout>
</template>

<script>
import {
    useCartStore
} from '~~/store/cart'
import {useProductStore} from '~/store/products';
export default {
    data() {
        return {
            cartHydrated: false,
        }
    },
    computed: {
        cart() {
            return useCartStore().cart
        },
    },
    watch: {
        cart: {
            deep: true,
            handler(cart) {
                if (!this.cartHydrated || !process.client) {
                    return
                }
                useLocalForage().setItem('evacode_cart', JSON.stringify(cart))
            },
        },
    },
    async mounted() {
        const localForage = useLocalForage();
        const cart = await localForage.getItem('evacode_cart');
        const cartArray = JSON.parse(cart || '[]');
        if (cartArray?.length) {
            useCartStore().setInitialCart(cartArray);
        }
        this.cartHydrated = true
        const currency = await localForage.getItem('evacode_currency');
        if (currency) {
            useProductStore().setCurrency(JSON.parse(currency));
        }

        window.addEventListener('beforeunload', async (event) => {
            console.log('beforeunload', JSON.stringify(useCartStore().cart));
            await localForage.setItem('evacode_cart', JSON.stringify(useCartStore().cart));
            await localForage.setItem('evacode_currency', JSON.stringify(useProductStore().changeCurrency));
        });
    },
}
</script>
