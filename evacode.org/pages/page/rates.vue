<template>
  <Header />
  <div class="rates-lux">
    <section class="rates-lux__hero">
      <div class="container">
        <p class="rates-lux__brand">EvaCode</p>
        <h1 class="rates-lux__title">Курсы валют</h1>
        <p class="rates-lux__lead">
          Официальные курсы магазина. Учёт в корейских вонах (₩), продажа — в любой из валют ниже.
        </p>
      </div>
    </section>

    <section class="rates-lux__body">
      <div class="container">
        <p v-if="pending" class="rates-lux__status">Загружаем курсы…</p>
        <p v-else-if="error" class="rates-lux__status rates-lux__status--error">{{ error }}</p>

        <template v-else>
          <p class="rates-lux__meta">
            База: <strong>KRW</strong>
            <span v-if="updatedAt"> · обновлено {{ formatUpdated(updatedAt) }}</span>
          </p>

          <div class="rates-lux__calc">
            <label class="rates-lux__label" for="rates-krw-amount">Сумма в вонах</label>
            <div class="rates-lux__field">
              <input
                id="rates-krw-amount"
                v-model="amountInput"
                type="text"
                inputmode="decimal"
                autocomplete="off"
                class="rates-lux__input"
                placeholder="77000"
              >
              <span class="rates-lux__suffix">₩</span>
            </div>
            <p class="rates-lux__hint">Введите цену товара в ₩ — ниже стоимость по всем валютам.</p>
          </div>

          <div class="rates-lux__table-wrap" role="region" aria-label="Курсы и пересчёт">
            <table class="rates-lux__table">
              <thead>
                <tr>
                  <th scope="col">Валюта</th>
                  <th scope="col">Курс (за 1 ₩)</th>
                  <th scope="col">Сумма</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <span class="rates-lux__quote">KRW</span>
                    <span class="rates-lux__name">Корейская вона</span>
                  </td>
                  <td>1</td>
                  <td class="rates-lux__amount">{{ formatMoney(amountKrw, 'KRW', '₩') }}</td>
                </tr>
                <tr v-for="row in rates" :key="row.quote">
                  <td>
                    <span class="rates-lux__quote">{{ row.quote }}</span>
                    <span class="rates-lux__name">{{ row.name || row.quote }}</span>
                  </td>
                  <td>{{ formatRate(row.rate) }}</td>
                  <td class="rates-lux__amount">
                    {{ formatMoney(amountKrw * Number(row.rate), row.quote, row.symbol) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p class="rates-lux__note">
            Курсы утверждаются EvaCode и могут отличаться от биржевых и банковских.
            Партнёрам и приложениям: <code>GET /api/core/currency-pairs/</code>
          </p>
        </template>
      </div>
    </section>
  </div>
</template>

<script setup>
useHead({
  title: 'Курсы валют — EvaCode',
  meta: [
    {
      name: 'description',
      content: 'Официальные курсы EvaCode: пересчёт цены в вонах в рубли, доллары, евро, тенге и другие валюты.',
    },
  ],
});

const config = useRuntimeConfig();
const amountInput = ref('77000');
const rates = ref([]);
const updatedAt = ref(null);
const pending = ref(true);
const error = ref('');

const amountKrw = computed(() => {
  const raw = String(amountInput.value || '').replace(/\s/g, '').replace(',', '.');
  const n = Number(raw);
  return Number.isFinite(n) && n >= 0 ? n : 0;
});

const formatRate = (rate) => {
  const n = Number(rate);
  if (!Number.isFinite(n)) return '—';
  return n.toLocaleString('ru-RU', { maximumFractionDigits: 10 });
};

const formatMoney = (value, currency, symbol) => {
  const n = Number(value);
  if (!Number.isFinite(n)) return '—';
  const digits = currency === 'KRW' || currency === 'UZS' ? 0 : currency === 'KZT' || currency === 'KGS' ? 0 : 2;
  const rounded = digits === 0 ? Math.round(n) : Math.round(n * 100) / 100;
  const formatted = rounded.toLocaleString('ru-RU', {
    minimumFractionDigits: digits === 0 ? 0 : 2,
    maximumFractionDigits: digits === 0 ? 0 : 2,
  });
  const sym = symbol || currency;
  if (currency === 'USD' || currency === 'EUR') {
    return `${sym}${formatted}`;
  }
  return `${formatted} ${sym}`;
};

const formatUpdated = (iso) => {
  try {
    return new Date(iso).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
};

const { data, error: fetchError } = await useAsyncData('currency-pairs', () =>
  $fetch(`${config.public.apiBase}/core/currency-pairs/`),
);

if (fetchError.value) {
  error.value = 'Не удалось загрузить курсы. Попробуйте позже.';
  pending.value = false;
} else {
  rates.value = data.value?.rates || [];
  updatedAt.value = data.value?.updated_at || null;
  pending.value = false;
}
</script>
