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
            База учёта: <strong>KRW</strong>
            · на экране курс за <strong>1000 ₩</strong>
            <span v-if="updatedAt"> · обновлено {{ formatUpdated(updatedAt) }}</span>
          </p>

          <div class="rates-lux__calc">
            <label class="rates-lux__label" for="rates-amount">Сумма для расчёта</label>
            <div class="rates-lux__controls">
              <div class="rates-lux__field">
                <input
                  id="rates-amount"
                  v-model="amountInput"
                  type="text"
                  inputmode="decimal"
                  autocomplete="off"
                  class="rates-lux__input"
                  :placeholder="inputPlaceholder"
                >
                <span class="rates-lux__suffix">{{ inputSymbol }}</span>
              </div>
              <label class="rates-lux__select-wrap">
                <select
                  v-model="inputQuote"
                  class="rates-lux__select"
                  aria-label="Валюта ввода"
                >
                  <option
                    v-for="opt in inputOptions"
                    :key="opt.quote"
                    :value="opt.quote"
                  >
                    {{ opt.quote }} — {{ opt.name }}
                  </option>
                </select>
              </label>
            </div>
            <p class="rates-lux__hint">
              Пересчёт по коммерческому курсу EvaCode; сумма округляется вверх по правилам валюты.
            </p>
          </div>

          <div class="rates-lux__table-wrap" role="region" aria-label="Курсы и пересчёт">
            <table class="rates-lux__table">
              <thead>
                <tr>
                  <th scope="col">Валюта</th>
                  <th scope="col">Курс (за 1000 ₩)</th>
                  <th scope="col">Сумма</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in displayRows"
                  :key="row.quote"
                  :class="{ 'is-input': row.quote === inputQuote }"
                >
                  <td>
                    <span class="rates-lux__quote">{{ row.quote }}</span>
                    <span class="rates-lux__name">{{ row.name }}</span>
                  </td>
                  <td>{{ formatRatePerThousand(row.ratePerKrw) }}</td>
                  <td class="rates-lux__amount">
                    {{ formatMoney(rowAmount(row), row.quote, row.symbol) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <p class="rates-lux__note">
            В API — коммерческий курс за 1 ₩ (уже с наценкой из админки).
            Округление вверх — на итоговой цене. Партнёрам:
            <code>GET /api/core/currency-pairs/</code>
          </p>
        </template>
      </div>
    </section>
  </div>
</template>

<script setup>
import { convertKrwWithCurr, roundQuotePrice } from '~/utils/currencyPrice';

useHead({
  title: 'Курсы валют — EvaCode',
  meta: [
    {
      name: 'description',
      content: 'Официальные курсы EvaCode: пересчёт цены между вонами, рублями, долларами, евро, тенге и другими валютами.',
    },
  ],
});

const KRW_ROW = {
  quote: 'KRW',
  name: 'Корейская вона',
  symbol: '₩',
  rate: '1',
};

const config = useRuntimeConfig();
const amountInput = ref('77000');
const inputQuote = ref('KRW');
const rates = ref([]);
const updatedAt = ref(null);
const pending = ref(true);
const error = ref('');

const rateOfRow = (row) => {
  const rate = Number(row?.rate);
  return Number.isFinite(rate) && rate > 0 ? rate : 0;
};

const inputOptions = computed(() => [
  KRW_ROW,
  ...rates.value.map((row) => ({
    quote: row.quote,
    name: row.name || row.quote,
    symbol: row.symbol || row.quote,
    rate: row.rate,
  })),
]);

const inputMeta = computed(() =>
  inputOptions.value.find((row) => row.quote === inputQuote.value) || KRW_ROW,
);

const inputSymbol = computed(() => inputMeta.value.symbol || inputQuote.value);

const inputPlaceholder = computed(() => {
  if (inputQuote.value === 'KRW') return '77000';
  if (inputQuote.value === 'USD' || inputQuote.value === 'EUR') return '68';
  if (inputQuote.value === 'RUB') return '5704';
  return '1000';
});

const parsedAmount = computed(() => {
  const raw = String(amountInput.value || '').replace(/\s/g, '').replace(',', '.');
  const n = Number(raw);
  return Number.isFinite(n) && n >= 0 ? n : 0;
});

/** Через воны: введённая сумма / коммерческий rate. */
const amountKrw = computed(() => {
  const amount = parsedAmount.value;
  if (inputQuote.value === 'KRW') return amount;
  const rate = rateOfRow(inputMeta.value);
  if (!(rate > 0)) return 0;
  return amount / rate;
});

const displayRows = computed(() => [
  {
    quote: 'KRW',
    name: 'Корейская вона',
    symbol: '₩',
    ratePerKrw: 1,
    curr: 1,
  },
  ...rates.value.map((row) => {
    const rate = Number(row.rate);
    return {
      quote: row.quote,
      name: row.name || row.quote,
      symbol: row.symbol || row.quote,
      ratePerKrw: rate,
      curr: rate,
    };
  }),
]);

const formatRatePerThousand = (ratePerKrw) => {
  const n = Number(ratePerKrw) * 1000;
  if (!Number.isFinite(n)) return '—';
  return n.toLocaleString('ru-RU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
};

const formatMoney = (value, currency, symbol) => {
  const n = Number(value);
  if (!Number.isFinite(n)) return '—';
  const digits = currency === 'USD' || currency === 'EUR' ? 2 : 0;
  const formatted = n.toLocaleString('ru-RU', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
  const sym = symbol || currency;
  if (currency === 'USD' || currency === 'EUR') {
    return `${sym}${formatted}`;
  }
  return `${formatted} ${sym}`;
};

const rowAmount = (row) => convertKrwWithCurr(amountKrw.value, row.quote, row.curr);

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

const formatInputValue = (value, quote) => {
  const rounded = roundQuotePrice(quote, value);
  const digits = quote === 'USD' || quote === 'EUR' ? 2 : 0;
  if (digits === 0) return String(Math.round(rounded));
  return Number(rounded).toFixed(2);
};

const rateOf = (quote) => {
  if (quote === 'KRW') return 1;
  const row = rates.value.find((item) => item.quote === quote);
  return rateOfRow(row);
};

const toKrw = (amount, quote) => {
  if (quote === 'KRW') return amount;
  const rate = rateOf(quote);
  return rate > 0 ? amount / rate : 0;
};

watch(inputQuote, (nextQuote, prevQuote) => {
  if (!prevQuote || nextQuote === prevQuote) return;
  const amount = parsedAmount.value;
  const krw = toKrw(amount, prevQuote);
  const nextRate = rateOf(nextQuote);
  if (nextQuote !== 'KRW' && nextRate <= 0) return;
  const converted = nextQuote === 'KRW' ? krw : krw * nextRate;
  amountInput.value = formatInputValue(converted, nextQuote);
});

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
