<template>
  <div v-if="currentCurrency.value !== 'KRW'" class="currency-warning">
      <h4>
          Курс валют меняется в течение дня. <br/>Точную сумму уточняйте у консультанта, на момент оплаты.
      </h4>
  </div>
</template>

<script setup>
import {useProductStore} from '~/store/products';

const currentCurrency = ref(useProductStore().changeCurrency);

</script>
