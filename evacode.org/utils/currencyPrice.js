/**
 * Округление продажных цен вверх + пересчёт KRW→валюта.
 * Правила синхронизированы с core/currency_pricing.py
 */

function ceilToStep(amount, step) {
  if (!(amount > 0)) return 0;
  return Math.ceil(amount / step) * step;
}

function roundUpHalfOr99(amount) {
  if (!(amount > 0)) return 0;
  const whole = Math.floor(amount);
  for (let w = whole; w < whole + 4; w += 1) {
    for (const ending of [0.5, 0.99]) {
      const cand = w + ending;
      if (cand + 1e-9 >= amount) return Math.round(cand * 100) / 100;
    }
  }
  return amount;
}

function roundUp50Or90(amount) {
  if (!(amount > 0)) return 0;
  let block = Math.floor(amount / 100) * 100;
  for (let i = 0; i < 8; i += 1) {
    for (const ending of [50, 90]) {
      const cand = block + ending;
      if (cand + 1e-9 >= amount) return cand;
    }
    block += 100;
  }
  return amount;
}

export function roundQuotePrice(quote, amount) {
  const code = String(quote || '').toUpperCase();
  const raw = Number(amount);
  if (!Number.isFinite(raw) || raw <= 0) return 0;

  if (code === 'USD' || code === 'EUR') {
    if (raw < 75) return roundUpHalfOr99(raw);
    if (raw < 250) return Math.ceil(raw);
    return ceilToStep(raw, 5);
  }

  if (code === 'RUB' || code === 'KZT' || code === 'KGS') {
    if (raw < 1000) return ceilToStep(raw, 10);
    if (raw < 10000) return roundUp50Or90(raw);
    return ceilToStep(raw, 100);
  }

  if (code === 'UZS') return ceilToStep(raw, 1000);
  if (code === 'KRW') return Math.ceil(raw);

  return Math.ceil(raw * 100) / 100;
}

/** curr — коммерческий курс с API (уже с наценкой из админки). */
export function convertKrwWithCurr(amountKrw, quote, curr) {
  const code = String(quote || 'KRW').toUpperCase();
  if (code === 'KRW') return roundQuotePrice('KRW', amountKrw);
  const rate = Number(curr);
  if (!Number.isFinite(rate) || rate <= 0) return 0;
  return roundQuotePrice(code, Number(amountKrw) * rate);
}
