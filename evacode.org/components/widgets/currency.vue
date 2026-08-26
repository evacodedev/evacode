<template>
    <MazDropdown
        :items="currencies"
        trigger="click"
    >
        {{ currentCurrency.value }}
    </MazDropdown>
</template>
<script setup>
import {useProductStore} from '~/store/products';
import useCurrencies from '~/composables/useCurrencies';
let currencies = ref([]);

const currentCurrency = ref(useProductStore().changeCurrency);

onMounted(async () => {
    const currenciesResp = await useCurrencies().getCurrencies();
    currencies.value = currenciesResp.map((currency) => ({
        label: currency.value,
        action: () => useProductStore().setCurrency(currency),
    }));
});
</script>
