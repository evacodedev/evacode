<template>
    <div class="currency-switcher">
        <MazDropdown
            :items="currencies"
            trigger="click"
        >
            <span class="currency-switcher__chip">
                <span v-if="currentSymbol" class="currency-switcher__symbol">{{ currentSymbol }}</span>
                <span class="currency-switcher__code">{{ currentCurrency.value }}</span>
            </span>
        </MazDropdown>
    </div>
</template>
<script setup>
import {useProductStore} from '~/store/products';
import useCurrencies from '~/composables/useCurrencies';

const GRAPHIC_SYMBOLS = {
    KRW: '₩',
    USD: '$',
    EUR: '€',
    RUB: '₽',
    KZT: '₸',
};

const graphicSymbol = (currency) => GRAPHIC_SYMBOLS[currency?.value] || '';

const productStore = useProductStore();
const currencies = ref([]);
const currentCurrency = computed(() => productStore.changeCurrency);
const currentSymbol = computed(() => graphicSymbol(currentCurrency.value));

onMounted(async () => {
    const currenciesResp = await useCurrencies().getCurrencies();
    currencies.value = (currenciesResp || []).map((currency) => {
        const item = { ...currency, symbol: graphicSymbol(currency) };
        return {
            label: item.symbol ? `${item.symbol} ${item.value}` : item.value,
            action: () => productStore.setCurrency(item),
        };
    });
});
</script>

<style scoped>
.currency-switcher {
    flex-shrink: 0;
    position: relative;
    z-index: 2;
}

.currency-switcher :deep(.m-dropdown-trigger),
.currency-switcher :deep(button) {
    min-width: 0;
    padding: 0;
    border: none;
    background: transparent;
    color: inherit !important;
}

.currency-switcher__chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    min-height: 36px;
    padding: 4px 10px;
    border: 1px solid var(--theme-deafult, #c43b3b);
    border-radius: 20px;
    background: #fff;
    color: #222;
    font-weight: 600;
    line-height: 1;
    white-space: nowrap;
}

.currency-switcher__symbol {
    font-size: 18px;
}

.currency-switcher__code {
    font-size: 13px;
    letter-spacing: 0.02em;
}

@media (max-width: 575px) {
    .currency-switcher__chip {
        min-height: 32px;
        padding: 3px 8px;
        gap: 4px;
    }

    .currency-switcher__symbol {
        font-size: 16px;
    }

    .currency-switcher__code {
        font-size: 12px;
    }
}
</style>
