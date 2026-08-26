<template>
<NuxtLayout >
    <Head></Head>
    <NuxtPage />
</NuxtLayout>
</template>

<script>
import {
    useCartStore
} from '~~/store/cart'
import {useProductStore} from '~/store/products';
export default {
    async mounted() {
        const localForage = useLocalForage();
        const cart = await localForage.getItem('evacode_cart');
        const cartArray = JSON.parse(cart || '[]');
        if (cartArray?.length) {
            useCartStore().setInitialCart(cartArray);
        }
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
