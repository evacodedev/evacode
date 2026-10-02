<template>
  <div>
    <Header />
    <AccountShell current="consultant">
      <nuxt-link
        :to="order ? { path: '/account/consultant/', query: { tab: consultantOrderTab(order) } } : '/account/consultant/'"
        class="consultant-back"
      >
        ← Все заказы клиентов
      </nuxt-link>

      <div v-if="loading" class="consultant-card" aria-hidden="true">
        <span class="skeleton-block consultant-row__skeleton" />
        <span class="skeleton-block consultant-row__skeleton consultant-row__skeleton--short" />
      </div>
      <p v-else-if="loadError" class="account-lux__status">{{ loadError }}</p>

      <template v-else>
        <div class="consultant-title">
          <div class="consultant-title__row">
            <h2 class="account-lux__heading">
              {{ isNew ? 'Новый заказ' : `Заказ для ${order?.client_name || 'клиента'}` }}
            </h2>
            <button
              class="consultant-btn consultant-share"
              type="button"
              :disabled="!lines.length"
              :title="lines.length ? shareHint : 'Сначала добавьте товары'"
              aria-label="Поделиться с клиентом"
              @click="shareWithClient"
            >
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="18" cy="5" r="2.6" />
                <circle cx="6" cy="12" r="2.6" />
                <circle cx="18" cy="19" r="2.6" />
                <path d="M8.3 13.3l7.4 4.4M15.7 6.3l-7.4 4.4" />
              </svg>
              Поделиться
            </button>
          </div>
          <p v-if="order" class="consultant-title__meta">
            <span class="consultant-status" :data-state="consultantOrderState(order)">
              {{ consultantOrderLabel(order) }}
            </span>
            <template v-if="order.business_ru_order_number"> Система заказов EvaCode №{{ order.business_ru_order_number }}</template>
            <template v-if="order.business_ru_reservation_number"> · резерв №{{ order.business_ru_reservation_number }}</template>
          </p>
        </div>

        <ol class="consultant-steps" aria-label="Шаги оформления">
          <li
            v-for="step in steps"
            :key="step.n"
            class="consultant-steps__item"
            :data-state="step.state"
            :aria-current="step.state === 'current' ? 'step' : undefined"
          >
            <a class="consultant-steps__link" :href="`#${step.anchor}`" @click.prevent="scrollToStep(step.anchor)">
              <span class="consultant-steps__num" aria-hidden="true">{{ step.state === 'done' ? '✓' : step.n }}</span>
              <span class="consultant-steps__text">
                <span class="consultant-steps__title">{{ step.title }}</span>
                <span class="consultant-steps__hint">{{ step.hint }}</span>
              </span>
            </a>
          </li>
        </ol>

        <!-- Шаг 1. Клиент -->
        <section id="step-client" class="consultant-card" aria-labelledby="consultant-client">
          <h3 id="consultant-client" class="consultant-card__title">
            <span class="consultant-card__step" :data-state="steps[0].state">{{ steps[0].state === 'done' ? '✓' : 1 }}</span>
            Клиент и доставка
          </h3>

          <template v-if="showLookup">
            <form class="consultant-lookup" @submit.prevent="onLookup">
              <CheckoutField
                v-model="lookupQuery"
                label="Найти по телефону или email"
                name="client_lookup"
                autocomplete="off"
                clearable
              />
              <button class="consultant-btn" type="submit" :disabled="lookupPending">
                {{ lookupPending ? 'Ищем…' : 'Найти' }}
              </button>
            </form>
            <p class="account-lux__hint">
              Только точное совпадение: полный номер с кодом страны или email целиком.
              <button
                v-if="clientSnapshot"
                type="button"
                class="consultant-link"
                @click="keepPreviousClient"
              >
                Оставить прежнего клиента
              </button>
            </p>
            <p v-if="lookupMessage" class="consultant-note" :class="{ 'is-error': lookupError }">{{ lookupMessage }}</p>
          </template>

          <fieldset v-if="editable && brMatches.length" class="consultant-br">
            <legend class="consultant-br__title">
              {{ brMatches.length > 1 ? 'В системе заказов EvaCode несколько клиентов — выберите нужного' : 'Клиент есть в системе заказов EvaCode' }}
            </legend>
            <label
              v-for="match in brMatches"
              :key="match.id"
              class="consultant-br__option"
              :class="{ 'is-active': brPartnerId === match.id }"
            >
              <input v-model="brPartnerId" type="radio" name="br_partner" :value="match.id">
              <span class="consultant-br__body">
                <span class="consultant-br__name">{{ match.name || 'Без имени' }}</span>
                <span class="consultant-row__meta">
                  {{ brMatchLabel(match) }} · заказов: {{ match.orders_count }}<template v-if="match.last_order">, последний №{{ match.last_order.number }} от {{ match.last_order.date }}</template>
                </span>
                <span v-if="match.phones.length || match.emails.length" class="consultant-row__meta">
                  {{ [...match.phones, ...match.emails].join(' · ') }}
                </span>
                <span v-if="match.address" class="consultant-br__address">
                  Адрес в системе заказов: {{ match.address }}
                  <button
                    v-if="shipping.method === 'ems'"
                    type="button"
                    class="consultant-link"
                    @click.prevent="insertBrAddress(match)"
                  >
                    Вставить в адрес
                  </button>
                </span>
              </span>
            </label>
            <p v-if="brTotal > brMatches.length" class="account-lux__hint">
              Показаны {{ brMatches.length }} из {{ brTotal }} совпадений: с этими контактами в системе заказов EvaCode есть ещё клиенты.
            </p>
            <p class="account-lux__hint">При оформлении заказ уйдёт на выбранного клиента, новый в системе заказов EvaCode не создастся.</p>
          </fieldset>
          <p v-else-if="editable && brError" class="consultant-note">{{ brError }}. При оформлении поищем клиента там ещё раз.</p>

          <div v-if="!showLookup && editable" class="consultant-client-summary">
            <span>
              Клиент привязан к черновику<template v-if="brPartnerId && !brMatches.length">, в системе заказов EvaCode — клиент id {{ brPartnerId }}</template>. Поля можно поправить ниже.
            </span>
            <button class="consultant-btn consultant-btn--small" type="button" @click="onChangeClient">
              Поменять клиента
            </button>
          </div>

          <div class="consultant-grid">
            <CheckoutField
              v-model="client.first_name"
              label="Имя и фамилия (латиницей)"
              name="first_name"
              :disabled="!editable"
              :error="errors.first_name"
              :submitted="submitted"
              @blur="latinize('first_name')"
            />
            <CheckoutField
              v-model="client.phone"
              label="Телефон"
              name="phone"
              type="tel"
              :disabled="!editable"
              :error="errors.phone"
              :submitted="submitted"
            />
            <CheckoutField
              v-model="client.email"
              label="Email (необязательно)"
              name="email"
              type="email"
              class="consultant-grid__wide"
              :disabled="!editable"
              :error="errors.email"
              :submitted="submitted"
            />
          </div>

          <div class="consultant-switch" role="radiogroup" aria-label="Доставка">
            <label class="consultant-switch__option" :class="{ 'is-active': shipping.method === 'ems' }">
              <input v-model="shipping.method" type="radio" value="ems" :disabled="!editable">
              EMS
            </label>
            <label class="consultant-switch__option" :class="{ 'is-active': shipping.method === 'pickup' }">
              <input v-model="shipping.method" type="radio" value="pickup" :disabled="!editable">
              Самовывоз в Корее
            </label>
          </div>
          <p v-if="errors.shipping" class="account-lux__error">{{ errors.shipping }}</p>

          <template v-if="shipping.method === 'ems'">
            <p class="account-lux__hint">
              Адрес попадёт на этикетку EMS — только латиница. Кириллицу переведём сами.
            </p>
            <div class="consultant-grid">
              <CheckoutField
                v-model="shipping.destination"
                label="Страна доставки"
                name="destination"
                :options="destinationOptions"
                :disabled="!editable"
                :error="errors.destination"
                :submitted="submitted"
              />
              <CheckoutField
                v-if="needsOtherCountry"
                v-model="client.country_other"
                label="Страна (латиницей)"
                name="country_other"
                :disabled="!editable"
                :error="errors.country"
                :submitted="submitted"
                @blur="latinize('country_other')"
              />
              <CheckoutField
                v-model="client.city"
                label="Город"
                name="city"
                :disabled="!editable"
                :error="errors.city"
                :submitted="submitted"
                @blur="latinize('city')"
              />
              <CheckoutField
                v-model="client.address"
                label="Улица, дом, квартира"
                name="address"
                class="consultant-grid__wide"
                :disabled="!editable"
                :error="errors.address"
                :submitted="submitted"
                @blur="latinize('address')"
              />
              <CheckoutField
                v-model="client.postal_code"
                label="Индекс"
                name="postal_code"
                :disabled="!editable"
                :error="errors.postal_code"
                :submitted="submitted"
                @blur="latinize('postal_code')"
              />
            </div>
          </template>

          <CheckoutField
            v-model="client.comment"
            label="Комментарий (необязательно)"
            name="comment"
            type="textarea"
            :rows="2"
            :disabled="!editable"
          />
        </section>

        <!-- Шаг 2. Товары и итог -->
        <section id="step-goods" class="consultant-card" aria-labelledby="consultant-goods">
          <h3 id="consultant-goods" class="consultant-card__title">
            <span class="consultant-card__step" :data-state="steps[1].state">{{ steps[1].state === 'done' ? '✓' : 2 }}</span>
            Товары
          </h3>

          <div v-if="editable" class="consultant-search">
            <div class="consultant-lookup">
              <CheckoutField
                v-model="goodsQuery"
                label="Поиск по каталогу"
                name="goods_search"
                clearable
                @update:model-value="onGoodsQuery"
                @clear="clearGoodsSearch"
              />
              <button
                v-if="cartAddable.length"
                class="consultant-btn"
                type="button"
                @click="addFromMyCart"
              >
                Из моей корзины
              </button>
            </div>
            <div v-if="goodsQuery.trim().length >= 2" class="consultant-results-panel">
              <div class="consultant-results-panel__head">
                <span>
                  {{ goodsSearching ? 'Ищем в каталоге…' : goodsResults.length ? `Результаты поиска: ${goodsResults.length}` : 'Ничего не нашли' }}
                </span>
                <button type="button" class="consultant-link" @click="clearGoodsSearch">Скрыть</button>
              </div>
              <ul v-if="!goodsSearching && goodsResults.length" class="consultant-results">
                <li v-for="good in goodsResults" :key="good.id" class="consultant-results__row">
                  <img
                    v-if="good.images?.[0]?.url"
                    :src="catalogImageUrl(good.images[0].url, { width: 96, height: 96 })"
                    :alt="good.title"
                    width="48"
                    height="48"
                    loading="lazy"
                  >
                  <span class="consultant-results__title">{{ good.title }}</span>
                  <span class="consultant-results__price">{{ formatQuotePrice(good.retail_price, 'KRW') }}</span>
                  <button
                    class="consultant-btn consultant-btn--small"
                    :class="{ 'consultant-btn--ghost': inOrder(good.id) }"
                    type="button"
                    :disabled="!good.stock"
                    @click="addGood(good)"
                  >
                    {{ !good.stock ? 'Нет в наличии' : inOrder(good.id) ? 'Ещё 1' : 'Добавить' }}
                  </button>
                </li>
              </ul>
            </div>
          </div>

          <p v-if="lines.length" class="consultant-lines__head">
            В заказе: {{ lines.length }} {{ pluralGoods(lines.length) }}, {{ linesQuantity }} шт.
          </p>
          <ul v-if="lines.length" class="consultant-lines">
            <li v-for="line in lines" :key="line.id" class="consultant-lines__row">
              <div class="account-lux__order-thumb">
                <img
                  v-if="line.image"
                  :src="catalogImageUrl(line.image, { width: 96, height: 96 })"
                  :alt="line.title"
                  width="48"
                  height="48"
                  loading="lazy"
                >
              </div>
              <span class="consultant-lines__title">{{ line.title }}</span>
              <div v-if="editable" class="consultant-qty">
                <button type="button" aria-label="Меньше" @click="changeQty(line, -1)">−</button>
                <span>{{ line.quantity }}</span>
                <button
                  type="button"
                  aria-label="Больше"
                  :disabled="line.stock != null && line.quantity >= line.stock"
                  @click="changeQty(line, 1)"
                >+</button>
              </div>
              <span v-else class="consultant-lines__qty">{{ line.quantity }} шт.</span>
              <span class="consultant-lines__price">{{ formatQuotePrice(line.price_krw * line.quantity, 'KRW') }}</span>
            </li>
          </ul>
          <p v-else class="account-lux__hint">Добавьте товары из каталога.</p>
          <p v-if="errors.cart" class="account-lux__error">{{ errors.cart }}</p>

          <div class="consultant-subblock" aria-labelledby="consultant-total">
          <h4 id="consultant-total" class="consultant-subblock__title">Итог</h4>
          <div class="consultant-grid">
            <CheckoutField
              v-model="displayCurrency"
              label="Валюта для клиента"
              name="display_currency"
              :options="currencyOptions"
              :disabled="!editable"
              :error="errors.display_currency"
              :submitted="submitted"
            />
          </div>
          <dl class="consultant-sum">
            <div>
              <dt>Товары</dt>
              <dd>
                {{ formatQuotePrice(goodsKrw, 'KRW') }}
                <span v-if="goodsPreview && previewTotalKrw == null" class="consultant-sum__alt">
                  ≈ {{ formatQuotePrice(goodsPreview, displayCurrency) }} без доставки
                </span>
              </dd>
            </div>
            <template v-if="showPreview && lines.length">
              <div>
                <dt>Доставка</dt>
                <dd>
                  <span v-if="quote.loading" class="consultant-sum__alt">Считаем…</span>
                  <span v-else-if="quote.error" class="consultant-sum__error">{{ quote.error }}</span>
                  <span v-else-if="quote.shippingKrw == null" class="consultant-sum__alt">Выберите страну доставки</span>
                  <template v-else>{{ quote.shippingKrw ? formatQuotePrice(quote.shippingKrw, 'KRW') : 'Бесплатно' }}</template>
                </dd>
              </div>
              <div v-if="previewTotalKrw != null" class="is-total">
                <dt>К оплате</dt>
                <dd>
                  {{ formatQuotePrice(previewTotalKrw, 'KRW') }}
                  <span v-if="previewTotalDisplay" class="consultant-sum__alt">
                    ≈ {{ formatQuotePrice(previewTotalDisplay, displayCurrency) }}
                  </span>
                </dd>
              </div>
            </template>
            <div v-if="order && !dirty">
              <dt>Доставка</dt>
              <dd>{{ order.shipping?.shipping_krw ? formatQuotePrice(order.shipping.shipping_krw, 'KRW') : 'Бесплатно' }}</dd>
            </div>
            <div v-if="order && !dirty" class="is-total">
              <dt>К оплате</dt>
              <dd>
                {{ formatQuotePrice(order.amount_krw, 'KRW') }}
                <span v-if="order.display_currency !== 'KRW' && order.display_amount" class="consultant-sum__alt">
                  ≈ {{ formatQuotePrice(order.display_amount, order.display_currency) }}
                </span>
              </dd>
            </div>
          </dl>
          <p v-if="formError" class="account-lux__error">{{ formError }}</p>
          <div v-if="editable" class="consultant-actions">
            <button class="consultant-btn consultant-btn--primary" type="button" :disabled="saving" @click="onSave">
              {{ saving ? 'Сохраняем…' : 'Сохранить черновик' }}
            </button>
            <button
              v-if="order"
              class="consultant-btn consultant-btn--ghost"
              type="button"
              :disabled="saving"
              @click="onDelete"
            >
              Удалить черновик
            </button>
          </div>
          <p v-if="editable && (!order || dirty)" class="account-lux__hint consultant-subblock__hint">
            Оплата откроется после сохранения черновика.
          </p>
          </div>
        </section>

        <!-- Шаг 3. Оплата -->
        <section v-if="!order" id="step-payment" class="consultant-card is-locked" aria-labelledby="consultant-payments">
          <h3 id="consultant-payments" class="consultant-card__title">
            <span class="consultant-card__step" data-state="todo">3</span>
            Оплата
          </h3>
          <p class="account-lux__hint">Сохраните черновик — здесь появится форма для оплаты клиента и фото.</p>
        </section>
        <section v-else id="step-payment" class="consultant-card" aria-labelledby="consultant-payments">
          <h3 id="consultant-payments" class="consultant-card__title">
            <span class="consultant-card__step" :data-state="steps[2].state">{{ steps[2].state === 'done' ? '✓' : 3 }}</span>
            Оплата
          </h3>

          <template v-if="editable && !dirty && !order.payments?.length">
            <div v-if="!order.sent_to_client_at" class="consultant-send">
              <p class="consultant-send__text">
                Отправьте клиенту сумму к оплате:
                <strong>{{ formatQuotePrice(order.amount_krw, 'KRW') }}</strong>
                <template v-if="order.display_currency !== 'KRW' && order.display_amount">
                  ≈ {{ formatQuotePrice(order.display_amount, order.display_currency) }}
                </template>.
                Потом отметьте — заказ перейдёт во вкладку «Жду оплаты».
              </p>
              <button class="consultant-btn consultant-btn--primary" type="button" :disabled="sentPending" @click="onMarkSent(true)">
                {{ sentPending ? 'Сохраняем…' : 'Отправил клиенту на оплату' }}
              </button>
            </div>
            <p v-else class="consultant-note consultant-send__done">
              Отправлено клиенту {{ formatDateTime(order.sent_to_client_at) }} — ждём оплату.
              <button type="button" class="consultant-link" :disabled="sentPending" @click="onMarkSent(false)">
                Вернуть в черновики
              </button>
            </p>
          </template>

          <div v-if="order.payments?.length" class="consultant-paid">
          <p class="consultant-paid__title">
            Внесённые оплаты · {{ order.payments.length }}
          </p>
          <ul class="consultant-payments">
            <li v-for="row in order.payments" :key="row.id" class="consultant-payments__row">
              <button
                v-if="row.has_proof"
                class="consultant-proof"
                type="button"
                :aria-label="`Открыть фото оплаты ${row.proof_name}`"
                @click="openProof(row)"
              >
                <img v-if="proofThumbs[row.id]" :src="proofThumbs[row.id]" alt="" width="56" height="56">
                <span v-else>{{ row.proof_is_image ? '…' : 'PDF' }}</span>
              </button>
              <span v-else class="consultant-proof" aria-hidden="true">—</span>
              <div>
                <p class="consultant-payments__amount">
                  {{ formatQuotePrice(row.amount, row.currency) }}
                  <span v-if="row.currency !== 'KRW'" class="consultant-sum__alt">
                    = {{ formatQuotePrice(row.amount_krw, 'KRW') }}
                  </span>
                </p>
                <p class="consultant-row__meta">
                  {{ formatDateTime(row.created_at) }}
                  <template v-if="row.business_ru_payment_number"> · ПКО №{{ row.business_ru_payment_number }}</template>
                </p>
              </div>
              <div v-if="editable && !row.in_business_ru" class="consultant-payments__actions">
                <button
                  class="consultant-btn consultant-btn--small"
                  type="button"
                  :disabled="paymentPending"
                  @click="startEditPayment(row)"
                >
                  Изменить
                </button>
                <button
                  class="consultant-btn consultant-btn--small consultant-btn--ghost"
                  type="button"
                  :disabled="paymentPending"
                  @click="onDeletePayment(row)"
                >
                  Удалить
                </button>
              </div>

              <form
                v-if="editingPaymentId === row.id"
                class="consultant-pay-form"
                @submit.prevent="onEditPayment(row)"
              >
                <div class="consultant-grid">
                  <CheckoutField
                    v-model="paymentEdit.amount"
                    label="Сумма, которую получили"
                    name="payment_edit_amount"
                    :error="paymentEditErrors.amount"
                    :submitted="paymentEditSubmitted"
                  />
                  <CheckoutField
                    v-model="paymentEdit.currency"
                    label="Валюта оплаты"
                    name="payment_edit_currency"
                    :options="currencyOptions"
                    :error="paymentEditErrors.currency"
                    :submitted="paymentEditSubmitted"
                  />
                </div>
                <label class="consultant-file">
                  <input type="file" accept="image/*,application/pdf" @change="onEditProofPicked">
                  <span>{{ paymentEdit.file ? paymentEdit.file.name : 'Заменить фото (необязательно)' }}</span>
                </label>
                <p v-if="paymentEditErrors.proof" class="account-lux__error">{{ paymentEditErrors.proof }}</p>
                <p class="account-lux__hint">Сумму в ₩ пересчитаем по сегодняшнему курсу.</p>
                <div class="consultant-actions">
                  <button class="consultant-btn consultant-btn--primary" type="submit" :disabled="paymentPending">
                    {{ paymentPending ? 'Сохраняем…' : 'Сохранить оплату' }}
                  </button>
                  <button class="consultant-btn consultant-btn--ghost" type="button" @click="cancelEditPayment">
                    Отмена
                  </button>
                </div>
              </form>
            </li>
          </ul>

          <!-- Сверка -->
          <div v-if="check?.has_payments" class="consultant-check" :data-state="checkState">
            <dl class="consultant-sum">
              <div><dt>Сумма заказа</dt><dd>{{ formatQuotePrice(check.amount_krw, 'KRW') }}</dd></div>
              <div><dt>Получено</dt><dd>{{ formatQuotePrice(check.paid_krw, 'KRW') }}</dd></div>
              <div v-if="check.shortfall_krw" class="is-total">
                <dt>Не хватает</dt>
                <dd>
                  {{ formatQuotePrice(check.shortfall_krw, 'KRW') }}
                  <span v-if="check.shortfall_display" class="consultant-sum__alt">
                    ≈ {{ formatQuotePrice(check.shortfall_display.amount, check.shortfall_display.currency) }}
                  </span>
                </dd>
              </div>
              <div v-else-if="check.overpaid_krw"><dt>Переплата</dt><dd>{{ formatQuotePrice(check.overpaid_krw, 'KRW') }}</dd></div>
            </dl>
          </div>
          </div>

          <p v-if="check?.shortfall_krw && editable" class="consultant-note">
            Курс изменился или клиент оплатил не всё. Попросите доплату и добавьте её как ещё одну оплату — оформить заказ можно только после полной оплаты.
          </p>

          <p v-if="editable && dirty" class="account-lux__hint">Сначала сохраните изменения заказа.</p>

          <!-- Новая оплата -->
          <form v-if="editable && !dirty && showNewPayment" class="consultant-pay-new" @submit.prevent="onAddPayment">
            <p class="consultant-pay-new__title">
              <span class="consultant-pay-new__plus" aria-hidden="true">+</span>
              {{ newPaymentTitle }}
            </p>
            <p v-if="!order.payments?.length" class="account-lux__hint consultant-pay-new__hint">
              Внесите сумму, которую фактически прислал клиент, и приложите фото или скриншот оплаты.
            </p>
            <div class="consultant-grid">
              <CheckoutField
                v-model="payment.amount"
                label="Сумма, которую получили"
                name="payment_amount"
                :error="paymentErrors.amount"
                :submitted="paymentSubmitted"
              />
              <CheckoutField
                v-model="payment.currency"
                label="Валюта оплаты"
                name="payment_currency"
                :options="currencyOptions"
                :error="paymentErrors.currency"
                :submitted="paymentSubmitted"
              />
            </div>
            <label class="consultant-file">
              <input type="file" accept="image/*,application/pdf" @change="onProofPicked">
              <span>{{ payment.file ? payment.file.name : 'Фото или скриншот оплаты' }}</span>
            </label>
            <p v-if="paymentErrors.proof" class="account-lux__error">{{ paymentErrors.proof }}</p>
            <p v-if="paymentFormError" class="account-lux__error">{{ paymentFormError }}</p>
            <div class="consultant-actions">
              <button class="consultant-btn" type="submit" :disabled="paymentPending">
                {{ paymentPending ? 'Загружаем…' : 'Добавить оплату' }}
              </button>
              <button
                v-if="newPaymentOpen"
                class="consultant-btn consultant-btn--ghost"
                type="button"
                :disabled="paymentPending"
                @click="newPaymentOpen = false"
              >
                Отмена
              </button>
            </div>
          </form>
          <button
            v-else-if="editable && !dirty"
            type="button"
            class="consultant-pay-more"
            @click="newPaymentOpen = true"
          >
            + Добавить ещё оплату
          </button>

          <div v-if="editable" class="consultant-final">
            <button
              class="consultant-submit"
              :class="{ 'is-ready': readyToSubmit }"
              type="button"
              :disabled="!readyToSubmit || submitting"
              :aria-describedby="'consultant-submit-hint'"
              @click="onSubmit"
            >
              <svg v-if="readyToSubmit" viewBox="0 0 20 20" width="20" height="20" aria-hidden="true">
                <circle cx="10" cy="10" r="9" fill="none" stroke="currentColor" stroke-width="1.6" />
                <path d="M6 10.4l2.7 2.6L14 7.6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <svg v-else viewBox="0 0 20 20" width="18" height="18" aria-hidden="true">
                <rect x="4" y="9" width="12" height="8.5" rx="1.8" fill="none" stroke="currentColor" stroke-width="1.6" />
                <path d="M7 9V6.5a3 3 0 0 1 6 0V9" fill="none" stroke="currentColor" stroke-width="1.6" />
              </svg>
              Оплата подтверждена — оформить
            </button>
            <p id="consultant-submit-hint" class="consultant-final__hint" :class="{ 'is-ready': readyToSubmit }">
              {{ submitHint }}
            </p>
            <div v-if="check?.shortfall_krw && !dirty" class="consultant-actions">
              <button class="consultant-btn" type="button" @click="copyShortfall">
                {{ copied ? 'Скопировано' : 'Запросить доплату' }}
              </button>
            </div>
          </div>
          <p v-if="submitError" class="account-lux__error">{{ submitError }}</p>

          <template v-if="!editable">
            <p v-if="order.exporting" class="consultant-note">Передаём заказ в систему заказов EvaCode…</p>
            <div v-else-if="order.business_ru_error" class="consultant-note is-error">
              <p>Не удалось передать заказ в систему заказов EvaCode: {{ order.business_ru_error }}</p>
              <button class="consultant-btn consultant-btn--small" type="button" :disabled="submitting" @click="onSubmit">
                Повторить выгрузку
              </button>
            </div>
            <p v-else-if="order.business_ru_order_number" class="consultant-note">
              Номер в системе заказов EvaCode: №{{ order.business_ru_order_number }}<template v-if="order.underpaid_krw">, долг клиента {{ formatQuotePrice(order.underpaid_krw, 'KRW') }}</template>.
            </p>
            <p v-if="order.underpaid_reason" class="account-lux__hint">Причина без доплаты: {{ order.underpaid_reason }}</p>
          </template>
        </section>
      </template>

      <Teleport to="body">
        <div
          v-if="lightboxUrl"
          class="consultant-lightbox"
          role="dialog"
          aria-modal="true"
          aria-label="Фото оплаты"
          @click="lightboxUrl = ''"
        >
          <img :src="lightboxUrl" alt="Фото оплаты">
          <button type="button" class="consultant-lightbox__close" aria-label="Закрыть">×</button>
        </div>
      </Teleport>
    </AccountShell>
    <Footer />
  </div>
</template>

<script setup>
import { accountErrorMessage, useAuthStore } from '~/store/auth'
import { useCartStore } from '~/store/cart'
import { addressCountryOptions, countryNameFromCode } from '~/utils/account-address'
import { catalogImageUrl } from '~/utils/catalogImage'
import { convertKrwWithCurr, formatQuotePrice } from '~/utils/currencyPrice'
import { consultantOrderLabel, consultantOrderState, consultantOrderTab } from '~/utils/consultant-status'
import { prepareProofFile } from '~/utils/proof-image'
import { sharedCartUrl } from '~/utils/shared-cart'
import {
  KOREA_CODE,
  LATIN_ONLY_MESSAGE,
  OTHER_COUNTRY_CODE,
  countryNameForLabel,
  hasNonLatinLetters,
  parseSiteDeliveryText,
  transliterateCyrillic,
} from '~/utils/shipping-address'

definePageMeta({
  middleware: 'consultant-auth',
})

useHead({
  title: 'Заказ клиента',
  titleTemplate: '%s — Личный кабинет',
})
useNoIndex()

const LATIN_CLIENT_FIELDS = ['first_name', 'country_other', 'city', 'address', 'postal_code']
const EXPORT_POLL_MS = 3000
const EXPORT_POLL_LIMIT = 20

const route = useRoute()
const auth = useAuthStore()
const cartStore = useCartStore()
const { showHandoff, hideHandoff } = useHandoff()
const { notify, confirmAction } = useAppNotice()

const isNew = computed(() => route.params.id === 'new')
const loading = ref(true)
const loadError = ref('')
const order = ref(null)
const currencies = ref([{ code: 'KRW', name: 'Корейская вона' }])
const destinations = ref([])

const client = reactive({
  first_name: '',
  phone: '',
  email: '',
  country_other: '',
  city: '',
  address: '',
  postal_code: '',
  comment: '',
})
const shipping = reactive({ method: 'ems', destination: '' })
const displayCurrency = ref('KRW')
const lines = ref([])
const errors = reactive({})
const submitted = ref(false)
const formError = ref('')
const saving = ref(false)
const dirty = ref(false)
let hydrating = false

const lookupQuery = ref('')
const lookupPending = ref(false)
const lookupMessage = ref('')
const lookupError = ref(false)
const changingClient = ref(false)
const clientSnapshot = ref(null)
const brMatches = ref([])
const brTotal = ref(0)
const brError = ref('')
const brPartnerId = ref('')
const cartTransferred = ref([])

const goodsQuery = ref('')
const goodsResults = ref([])
const goodsSearching = ref(false)
let goodsTimer = null
let goodsRequestId = 0

const payment = reactive({ amount: '', currency: 'KRW', file: null })
const paymentErrors = reactive({ amount: '', currency: '', proof: '' })
const paymentSubmitted = ref(false)
const paymentPending = ref(false)
const paymentFormError = ref('')

const editingPaymentId = ref(null)
const paymentEdit = reactive({ amount: '', currency: 'KRW', file: null })
const paymentEditErrors = reactive({ amount: '', currency: '', proof: '' })
const paymentEditSubmitted = ref(false)

const proofThumbs = reactive({})
const lightboxUrl = ref('')

const sentPending = ref(false)
const submitting = ref(false)
const submitError = ref('')
const copied = ref(false)

const editable = computed(() => !order.value || order.value.is_draft)
const check = computed(() => order.value?.check || null)
const checkState = computed(() => {
  if (!check.value) return ''
  if (check.value.shortfall_krw) return 'short'
  return 'ok'
})
const readyToSubmit = computed(() =>
  Boolean(order.value?.is_draft && !dirty.value && check.value?.has_payments && !check.value.shortfall_krw),
)
const submitHint = computed(() => {
  if (dirty.value) return 'Сначала сохраните изменения заказа.'
  if (!check.value?.has_payments) return 'Кнопка станет активной, когда вы внесёте оплату клиента с фото.'
  if (check.value.shortfall_krw) {
    return `Не хватает ${formatQuotePrice(check.value.shortfall_krw, 'KRW')} — оформить можно только после доплаты.`
  }
  return 'Оплата сходится — заказ готов к передаче в EvaCode.'
})
const newPaymentOpen = ref(false)
const showNewPayment = computed(() =>
  !order.value?.payments?.length || Boolean(check.value?.shortfall_krw) || newPaymentOpen.value,
)
const newPaymentTitle = computed(() => {
  if (!order.value?.payments?.length) return 'Оплата клиента'
  if (check.value?.shortfall_krw) return 'Доплата клиента'
  return 'Ещё одна оплата'
})
const needsOtherCountry = computed(() => shipping.method === 'ems' && shipping.destination === OTHER_COUNTRY_CODE)

const clientReady = computed(() => {
  if (client.first_name.trim().length < 2 || client.phone.replace(/\D/g, '').length < 7) return false
  if (shipping.method !== 'ems') return true
  if (needsOtherCountry.value && !client.country_other.trim()) return false
  return Boolean(shipping.destination && client.city.trim() && client.address.trim() && client.postal_code.trim())
})
const goodsSaved = computed(() => Boolean(lines.value.length && order.value && !dirty.value))
const steps = computed(() => {
  const finished = Boolean(order.value && !order.value.is_draft)
  const done = [clientReady.value || finished, goodsSaved.value || finished, finished]
  const current = done.indexOf(false)

  let paymentHint = 'После сохранения черновика'
  if (finished) paymentHint = order.value.business_ru_order_number ? `Оформлен, №${order.value.business_ru_order_number}` : 'Оформлен'
  else if (order.value && !dirty.value) {
    if (!check.value?.has_payments) {
      paymentHint = order.value.sent_to_client_at ? 'Ждём оплату от клиента' : 'Отправьте клиенту сумму'
    } else if (check.value.shortfall_krw) paymentHint = `Не хватает ${formatQuotePrice(check.value.shortfall_krw, 'KRW')}`
    else paymentHint = 'Можно оформлять'
  }

  const rows = [
    {
      n: 1,
      title: 'Клиент',
      anchor: 'step-client',
      hint: done[0] ? client.first_name.trim() || 'Заполнено' : 'Имя, телефон, адрес',
    },
    {
      n: 2,
      title: 'Товары',
      anchor: 'step-goods',
      hint: done[1]
        ? `${linesQuantity.value} шт. · черновик сохранён`
        : lines.value.length ? `${linesQuantity.value} шт. · сохраните черновик` : 'Добавьте и сохраните',
    },
    { n: 3, title: 'Оплата', anchor: 'step-payment', hint: paymentHint },
  ]
  return rows.map((row, index) => ({
    ...row,
    state: done[index] ? 'done' : index === current ? 'current' : 'todo',
  }))
})

function scrollToStep(anchor) {
  const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  document.getElementById(anchor)?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' })
}
const destinationOptions = computed(() =>
  addressCountryOptions(destinations.value).filter((item) => item.value !== KOREA_CODE),
)
const currencyOptions = computed(() =>
  currencies.value.map((row) => ({ value: row.code, label: `${row.code} — ${row.name}` })),
)
const goodsKrw = computed(() =>
  lines.value.reduce((sum, line) => sum + Number(line.price_krw || 0) * Number(line.quantity || 0), 0),
)
const linesQuantity = computed(() => lines.value.reduce((sum, line) => sum + Number(line.quantity || 0), 0))
const showPreview = computed(() => editable.value && (!order.value || dirty.value))

function toDisplayCurrency(amountKrw) {
  if (displayCurrency.value === 'KRW' || !amountKrw) return 0
  const rate = currencies.value.find((row) => row.code === displayCurrency.value)?.rate
  return convertKrwWithCurr(amountKrw, displayCurrency.value, rate)
}

const goodsPreview = computed(() => (showPreview.value ? toDisplayCurrency(goodsKrw.value) : 0))

const quote = reactive({ loading: false, shippingKrw: null, error: '' })
let quoteTimer = null
let quoteRequestId = 0

const previewTotalKrw = computed(() => {
  if (!showPreview.value || quote.loading || quote.error || quote.shippingKrw == null || !lines.value.length) {
    return null
  }
  return goodsKrw.value + Number(quote.shippingKrw)
})
const previewTotalDisplay = computed(() =>
  previewTotalKrw.value == null ? 0 : toDisplayCurrency(previewTotalKrw.value),
)

function scheduleQuote() {
  clearTimeout(quoteTimer)
  const requestId = ++quoteRequestId
  quote.error = ''
  if (!lines.value.length || (shipping.method === 'ems' && !shipping.destination)) {
    quote.loading = false
    quote.shippingKrw = null
    return
  }
  quote.loading = true
  quoteTimer = setTimeout(() => fetchQuote(requestId), 500)
}

async function fetchQuote(requestId) {
  try {
    const data = await $fetch(`${useRuntimeConfig().public.apiBase}/market/shipping/quote/`, {
      method: 'POST',
      body: {
        cart: lines.value.map((line) => ({ id: line.id, quantity: line.quantity })),
        shipping: shipping.method === 'pickup'
          ? { method: 'pickup', destination: KOREA_CODE }
          : { method: 'ems', destination: shipping.destination },
      },
    })
    if (requestId !== quoteRequestId) return
    quote.shippingKrw = data?.shipping_krw ?? null
  } catch (error) {
    if (requestId !== quoteRequestId) return
    quote.shippingKrw = null
    quote.error = error?.data?.error || 'Не удалось посчитать доставку'
  } finally {
    if (requestId === quoteRequestId) quote.loading = false
  }
}

watch(
  () => [
    showPreview.value,
    shipping.method,
    shipping.destination,
    lines.value.map((line) => `${line.id}:${line.quantity}`).join(','),
  ],
  () => {
    if (showPreview.value) scheduleQuote()
  },
)
const showLookup = computed(() => editable.value && (!order.value || changingClient.value))
const cartAddable = computed(() =>
  cartStore.cartItems.filter(
    (item) => Number(item.retail_price) > 0 && item.stock !== 0 && !lines.value.some((line) => line.id === item.id),
  ),
)

watch([client, shipping, displayCurrency, lines, brPartnerId], () => {
  if (!hydrating) {
    dirty.value = true
  }
}, { deep: true })

function latinize(field) {
  if (client[field]) {
    client[field] = transliterateCyrillic(client[field])
  }
}

function clearErrors() {
  Object.keys(errors).forEach((key) => delete errors[key])
}

function hydrate(data) {
  hydrating = true
  order.value = data
  const c = data.client || {}
  const destination = data.shipping?.destination || ''
  Object.assign(client, {
    first_name: c.first_name || '',
    phone: c.phone || '',
    email: c.email || '',
    country_other: destination === OTHER_COUNTRY_CODE ? c.country || '' : '',
    city: c.city || '',
    address: c.address || '',
    postal_code: c.postal_code || '',
    comment: c.comment || '',
  })
  brPartnerId.value = c.business_ru_partner_id || ''
  shipping.method = data.shipping?.method || 'ems'
  shipping.destination = shipping.method === 'pickup' ? '' : destination
  displayCurrency.value = data.display_currency || 'KRW'
  lines.value = (data.items || []).map((item) => ({
    id: item.id,
    title: item.title,
    quantity: item.quantity,
    price_krw: item.price_krw,
    image: item.image,
    stock: item.stock,
  }))
  if (!payment.amount && data.display_currency) {
    payment.currency = data.display_currency
  }
  syncProofThumbs(data.payments || [])
  nextTick(() => {
    hydrating = false
    dirty.value = false
  })
}

function dropProofThumb(id) {
  if (proofThumbs[id]) {
    URL.revokeObjectURL(proofThumbs[id])
    delete proofThumbs[id]
  }
}

function syncProofThumbs(payments) {
  const ids = new Set(payments.map((row) => row.id))
  Object.keys(proofThumbs).forEach((id) => {
    if (!ids.has(Number(id))) dropProofThumb(id)
  })
  payments.forEach(async (row) => {
    if (!row.has_proof || !row.proof_is_image || proofThumbs[row.id]) return
    try {
      const blob = await auth.authFetch(row.proof_url, { responseType: 'blob' })
      if (!proofThumbs[row.id]) proofThumbs[row.id] = URL.createObjectURL(blob)
    } catch {
      // Миниатюра необязательна: по клику фото всё равно откроется.
    }
  })
}

function countryForPayload() {
  if (shipping.method !== 'ems') return ''
  if (needsOtherCountry.value) return client.country_other.trim()
  const name = countryNameFromCode(destinations.value, shipping.destination)
  return countryNameForLabel(shipping.destination, name) || name
}

function validate() {
  clearErrors()
  LATIN_CLIENT_FIELDS.forEach(latinize)
  if (client.first_name.trim().length < 2) errors.first_name = 'Укажите имя клиента'
  if (client.phone.replace(/\D/g, '').length < 7) errors.phone = 'Укажите телефон клиента'
  if (client.email.trim() && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(client.email.trim())) {
    errors.email = 'Укажите корректный email'
  }
  if (shipping.method === 'ems') {
    if (!shipping.destination) errors.destination = 'Укажите страну'
    if (needsOtherCountry.value && !client.country_other.trim()) errors.country = 'Укажите страну'
    if (!client.city.trim()) errors.city = 'Укажите город'
    if (!client.address.trim()) errors.address = 'Укажите адрес'
    if (!client.postal_code.trim()) errors.postal_code = 'Укажите индекс'
  }
  const latinFields = shipping.method === 'ems' ? LATIN_CLIENT_FIELDS : ['first_name']
  latinFields.forEach((field) => {
    const key = field === 'country_other' ? 'country' : field
    if (!errors[key] && hasNonLatinLetters(client[field])) {
      errors[key] = LATIN_ONLY_MESSAGE
    }
  })
  if (!lines.value.length) errors.cart = 'Добавьте товары'
  return !Object.keys(errors).length
}

function draftPayload() {
  return {
    client: {
      first_name: client.first_name.trim(),
      phone: client.phone.trim(),
      email: client.email.trim(),
      country: countryForPayload(),
      city: shipping.method === 'ems' ? client.city.trim() : '',
      address: shipping.method === 'ems' ? client.address.trim() : '',
      postal_code: shipping.method === 'ems' ? client.postal_code.trim() : '',
      comment: client.comment.trim(),
      business_ru_partner_id: brPartnerId.value,
    },
    shipping: {
      method: shipping.method,
      destination: shipping.method === 'pickup' ? KOREA_CODE : shipping.destination,
    },
    display_currency: displayCurrency.value,
    cart: lines.value.map((line) => ({ id: line.id, quantity: line.quantity })),
  }
}

function applyServerErrors(error, fallback) {
  const data = error?.data
  if (data?.errors && typeof data.errors === 'object') {
    Object.assign(errors, data.errors)
    return Object.keys(data.errors).some((key) => ['cart', 'shipping', 'display_currency'].includes(key))
      ? ''
      : 'Проверьте поля формы'
  }
  return accountErrorMessage(error, fallback)
}

async function onSave() {
  submitted.value = true
  formError.value = ''
  if (!validate() || saving.value) {
    if (Object.keys(errors).length) formError.value = 'Проверьте поля формы'
    return
  }
  saving.value = true
  try {
    const path = order.value ? `/market/consultant/orders/${order.value.id}/` : '/market/consultant/orders/'
    const data = await auth.authFetch(path, {
      method: order.value ? 'PUT' : 'POST',
      body: draftPayload(),
    })
    submitted.value = false
    hydrate(data)
    clearTransferredCart()
    notify('Черновик сохранён')
    await navigateTo({ path: '/account/consultant/', query: { tab: consultantOrderTab(order.value) } })
  } catch (error) {
    formError.value = applyServerErrors(error, 'Не удалось сохранить черновик')
  } finally {
    saving.value = false
  }
}

async function onMarkSent(sent) {
  if (!order.value || sentPending.value) return
  sentPending.value = true
  try {
    hydrate(await auth.authFetch(`/market/consultant/orders/${order.value.id}/sent/`, {
      method: 'POST',
      body: { sent },
    }))
    notify(sent ? 'Заказ во вкладке «Жду оплаты»' : 'Заказ вернулся в черновики')
  } catch (error) {
    notify(accountErrorMessage(error, 'Не удалось изменить статус'))
  } finally {
    sentPending.value = false
  }
}

function clearTransferredCart() {
  const saved = new Set(lines.value.map((line) => line.id))
  const moved = new Set(cartTransferred.value.filter((id) => saved.has(id)))
  cartTransferred.value = []
  if (moved.size) {
    cartStore.setInitialCart(cartStore.cart.filter((item) => !moved.has(item.id)))
  }
}

async function onDelete() {
  if (!order.value) return
  const ok = await confirmAction({
    title: 'Удалить черновик?',
    text: 'Оплаты и фото тоже удалятся. Вернуть черновик будет нельзя.',
    confirmLabel: 'Удалить',
    danger: true,
  })
  if (!ok) return
  saving.value = true
  try {
    await auth.authFetch(`/market/consultant/orders/${order.value.id}/`, { method: 'DELETE' })
    notify('Черновик удалён')
    await navigateTo('/account/consultant/')
  } catch (error) {
    formError.value = accountErrorMessage(error, 'Не удалось удалить черновик')
  } finally {
    saving.value = false
  }
}

function hasClientData() {
  return CLIENT_FIELDS.some((field) => client[field].trim()) || Boolean(shipping.destination)
}

function clearClientFields() {
  CLIENT_FIELDS.forEach((field) => { client[field] = '' })
  shipping.destination = ''
  applyBusinessRu(null)
  clearErrors()
}

async function onLookup() {
  const q = lookupQuery.value.trim()
  if (!q || lookupPending.value) return
  if (hasClientData()) {
    const ok = await confirmAction({
      title: 'Начать новый поиск?',
      text: 'Имя, телефон, email и адрес клиента очистятся. Если клиент не найдётся, их нужно будет заполнить заново.',
      confirmLabel: 'Очистить и искать',
    })
    if (!ok) return
    clearClientFields()
  }
  lookupMessage.value = ''
  lookupError.value = false
  lookupPending.value = true
  try {
    const data = await auth.authFetch('/market/consultant/clients/lookup/', { query: { q } })
    applyBusinessRu(data?.business_ru)
    const isEmail = q.includes('@')
    const found = data?.client
    const best = brMatches.value[0]
    if (found) {
      Object.assign(client, {
        first_name: found.first_name || client.first_name,
        phone: found.phone || client.phone,
        email: found.email || client.email,
        city: found.city || client.city,
        address: found.address || client.address,
        postal_code: found.postal_code || client.postal_code,
      })
      if (found.shipping_method === 'pickup') {
        shipping.method = 'pickup'
      } else if (found.destination && found.destination !== KOREA_CODE) {
        shipping.method = 'ems'
        shipping.destination = found.destination
        if (found.destination === OTHER_COUNTRY_CODE) {
          client.country_other = found.country || ''
        }
      }
    } else if (best) {
      Object.assign(client, {
        first_name: best.name || client.first_name,
        phone: isEmail ? best.phones[0] || client.phone : q,
        email: isEmail ? q : best.emails[0] || client.email,
      })
    }
    LATIN_CLIENT_FIELDS.forEach(latinize)
    if (found && best) {
      lookupMessage.value = 'Нашли на сайте и в системе заказов EvaCode. Данные подставлены с сайта, проверьте их.'
    } else if (best) {
      lookupMessage.value = 'На сайте клиента нет, нашли в системе заказов EvaCode. Имя и контакты подставлены, адрес заполните сами.'
    } else {
      lookupMessage.value = brError.value
        ? 'Нашли на сайте. Данные подставлены, проверьте их.'
        : 'Нашли на сайте. В системе заказов EvaCode совпадений нет — при оформлении создадим клиента там.'
    }
    notify('Клиент найден')
  } catch (error) {
    applyBusinessRu(error?.data?.business_ru)
    lookupError.value = true
    lookupMessage.value = accountErrorMessage(error, 'Клиент не найден')
  } finally {
    lookupPending.value = false
  }
}

function applyBusinessRu(result) {
  brMatches.value = result?.matches || []
  brTotal.value = result?.total || 0
  brError.value = result?.error || ''
  brPartnerId.value = brMatches.value[0]?.id || ''
}

const BR_MATCH_LABELS = {
  'email+phone': 'совпали email и телефон',
  email: 'совпал email',
  phone: 'совпал телефон',
}

function brMatchLabel(match) {
  return BR_MATCH_LABELS[match.match] || 'совпадение'
}

function insertBrAddress(match) {
  const parsed = parseSiteDeliveryText(match.address, destinations.value)
  if (parsed) {
    shipping.method = 'ems'
    shipping.destination = parsed.destination
    Object.assign(client, { city: parsed.city, address: parsed.address, postal_code: parsed.postalCode })
    LATIN_CLIENT_FIELDS.forEach(latinize)
    ;['destination', 'city', 'address', 'postal_code'].forEach((key) => delete errors[key])
    notify('Адрес из системы заказов разложен по полям. Проверьте его.')
    return
  }
  client.address = transliterateCyrillic(match.address)
  notify('Адрес вставлен одной строкой. Разнесите страну, город и индекс по полям.')
}

const CLIENT_FIELDS = ['first_name', 'phone', 'email', 'country_other', 'city', 'address', 'postal_code']

async function onChangeClient() {
  const ok = await confirmAction({
    title: 'Поменять клиента?',
    text: 'Поля клиента очистятся. Черновик изменится только после сохранения.',
    confirmLabel: 'Поменять',
  })
  if (!ok) return
  clientSnapshot.value = {
    client: { ...client },
    shipping: { ...shipping },
    brPartnerId: brPartnerId.value,
  }
  clearClientFields()
  lookupQuery.value = ''
  lookupMessage.value = ''
  lookupError.value = false
  changingClient.value = true
}

function keepPreviousClient() {
  const snapshot = clientSnapshot.value
  if (!snapshot) return
  Object.assign(client, snapshot.client)
  Object.assign(shipping, snapshot.shipping)
  applyBusinessRu(null)
  brPartnerId.value = snapshot.brPartnerId
  clientSnapshot.value = null
  changingClient.value = false
  lookupMessage.value = ''
  clearErrors()
}

function onGoodsQuery() {
  clearTimeout(goodsTimer)
  const q = goodsQuery.value.trim()
  if (q.length < 2) {
    goodsResults.value = []
    goodsSearching.value = false
    return
  }
  goodsSearching.value = true
  goodsTimer = setTimeout(() => searchGoods(q), 300)
}

async function searchGoods(q) {
  const requestId = ++goodsRequestId
  try {
    const data = await $fetch(`${useRuntimeConfig().public.apiBase}/market/goods/`, {
      query: { search: q, page_size: 12 },
    })
    if (requestId === goodsRequestId) {
      goodsResults.value = (data?.results || []).filter((good) => Number(good.retail_price) > 0)
    }
  } catch {
    if (requestId === goodsRequestId) goodsResults.value = []
  } finally {
    if (requestId === goodsRequestId) goodsSearching.value = false
  }
}

function addLine(good, quantity = 1) {
  const existing = lines.value.find((line) => line.id === good.id)
  const stock = good.stock == null ? null : Number(good.stock)
  if (existing) {
    existing.quantity = stock == null ? existing.quantity + quantity : Math.min(stock, existing.quantity + quantity)
    return
  }
  lines.value.push({
    id: good.id,
    title: good.title,
    quantity: stock == null ? quantity : Math.min(stock, quantity),
    price_krw: Number(good.retail_price || 0),
    image: good.images?.[0]?.url || good.image || '',
    stock,
  })
}

function clearGoodsSearch() {
  clearTimeout(goodsTimer)
  goodsRequestId += 1
  goodsQuery.value = ''
  goodsResults.value = []
  goodsSearching.value = false
}

function inOrder(goodId) {
  return lines.value.some((line) => line.id === goodId)
}

function pluralGoods(count) {
  const mod10 = count % 10
  const mod100 = count % 100
  if (mod10 === 1 && mod100 !== 11) return 'товар'
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 'товара'
  return 'товаров'
}

function addGood(good) {
  addLine(good, 1)
  delete errors.cart
}

function addFromMyCart() {
  const items = cartAddable.value
  items.forEach((item) => {
    addLine(item, Number(item.quantity) || 1)
    if (!cartTransferred.value.includes(item.id)) cartTransferred.value.push(item.id)
  })
  delete errors.cart
  if (items.length) {
    notify(`Добавлено из корзины: ${items.length}. Корзина очистится после сохранения.`)
  }
}

async function addCartOnArrival() {
  if (route.query.from !== 'cart') return
  if (!cartStore.cart.length) {
    try {
      const stored = JSON.parse((await useLocalForage().getItem('evacode_cart')) || '[]')
      if (stored?.length && !cartStore.cart.length) cartStore.setInitialCart(stored)
    } catch {
      return
    }
  }
  if (cartAddable.value.length) addFromMyCart()
}

function changeQty(line, delta) {
  const next = line.quantity + delta
  if (next <= 0) {
    lines.value = lines.value.filter((row) => row.id !== line.id)
    return
  }
  if (line.stock != null && next > line.stock) return
  line.quantity = next
}

async function onProofPicked(event) {
  paymentErrors.proof = ''
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  try {
    payment.file = await prepareProofFile(file)
  } catch (error) {
    payment.file = null
    paymentErrors.proof = error.message
    paymentSubmitted.value = true
  }
}

async function onAddPayment() {
  paymentSubmitted.value = true
  paymentFormError.value = ''
  const amount = Number(String(payment.amount).replace(/\s/g, '').replace(',', '.'))
  paymentErrors.amount = amount > 0 ? '' : 'Укажите сумму оплаты'
  paymentErrors.currency = payment.currency ? '' : 'Выберите валюту'
  paymentErrors.proof = payment.file ? paymentErrors.proof : 'Приложите фото подтверждения оплаты'
  if (paymentErrors.amount || paymentErrors.currency || paymentErrors.proof || paymentPending.value) {
    return
  }
  paymentPending.value = true
  try {
    const body = new FormData()
    body.append('amount', String(amount))
    body.append('currency', payment.currency)
    body.append('proof', payment.file, payment.file.name)
    const data = await auth.authFetch(`/market/consultant/orders/${order.value.id}/payments/`, {
      method: 'POST',
      body,
    })
    payment.amount = ''
    payment.file = null
    paymentSubmitted.value = false
    newPaymentOpen.value = false
    hydrate(data)
    notify('Оплата добавлена')
  } catch (error) {
    const data = error?.data
    if (data?.errors) {
      paymentErrors.amount = data.errors.amount || ''
      paymentErrors.currency = data.errors.currency || ''
      paymentErrors.proof = data.errors.proof || ''
    } else if (Number(error?.statusCode || error?.status) === 413) {
      paymentFormError.value = 'Файл слишком большой. Приложите скриншот оплаты.'
    } else {
      paymentFormError.value = accountErrorMessage(error, 'Не удалось добавить оплату')
    }
  } finally {
    paymentPending.value = false
  }
}

async function onDeletePayment(row) {
  const ok = await confirmAction({
    title: 'Удалить оплату?',
    text: `${formatQuotePrice(row.amount, row.currency)} и фото к ней удалятся.`,
    confirmLabel: 'Удалить',
    danger: true,
  })
  if (!ok) return
  paymentPending.value = true
  try {
    const data = await auth.authFetch(`/market/consultant/orders/${order.value.id}/payments/${row.id}/`, {
      method: 'DELETE',
    })
    if (editingPaymentId.value === row.id) cancelEditPayment()
    hydrate(data)
    notify('Оплата удалена')
  } catch (error) {
    paymentFormError.value = accountErrorMessage(error, 'Не удалось удалить оплату')
  } finally {
    paymentPending.value = false
  }
}

function startEditPayment(row) {
  editingPaymentId.value = row.id
  Object.assign(paymentEdit, { amount: String(Number(row.amount)), currency: row.currency, file: null })
  Object.assign(paymentEditErrors, { amount: '', currency: '', proof: '' })
  paymentEditSubmitted.value = false
}

function cancelEditPayment() {
  editingPaymentId.value = null
  paymentEdit.file = null
}

async function onEditProofPicked(event) {
  paymentEditErrors.proof = ''
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  try {
    paymentEdit.file = await prepareProofFile(file)
  } catch (error) {
    paymentEdit.file = null
    paymentEditErrors.proof = error.message
    paymentEditSubmitted.value = true
  }
}

async function onEditPayment(row) {
  paymentEditSubmitted.value = true
  const amount = Number(String(paymentEdit.amount).replace(/\s/g, '').replace(',', '.'))
  paymentEditErrors.amount = amount > 0 ? '' : 'Укажите сумму оплаты'
  paymentEditErrors.currency = paymentEdit.currency ? '' : 'Выберите валюту'
  if (paymentEditErrors.amount || paymentEditErrors.currency || paymentEditErrors.proof || paymentPending.value) {
    return
  }
  paymentPending.value = true
  try {
    const body = new FormData()
    body.append('amount', String(amount))
    body.append('currency', paymentEdit.currency)
    const replacesProof = Boolean(paymentEdit.file)
    if (replacesProof) {
      body.append('proof', paymentEdit.file, paymentEdit.file.name)
    }
    const data = await auth.authFetch(`/market/consultant/orders/${order.value.id}/payments/${row.id}/`, {
      method: 'PUT',
      body,
    })
    if (replacesProof) dropProofThumb(row.id)
    cancelEditPayment()
    hydrate(data)
    notify('Оплата изменена')
  } catch (error) {
    const data = error?.data
    if (data?.errors) {
      paymentEditErrors.amount = data.errors.amount || ''
      paymentEditErrors.currency = data.errors.currency || ''
      paymentEditErrors.proof = data.errors.proof || ''
    } else if (Number(error?.statusCode || error?.status) === 413) {
      paymentEditErrors.proof = 'Файл слишком большой. Приложите скриншот оплаты.'
    } else {
      paymentEditErrors.proof = accountErrorMessage(error, 'Не удалось изменить оплату')
    }
  } finally {
    paymentPending.value = false
  }
}

async function openProof(row) {
  if (proofThumbs[row.id]) {
    lightboxUrl.value = proofThumbs[row.id]
    return
  }
  const win = row.proof_is_image ? null : window.open('', '_blank')
  try {
    const blob = await auth.authFetch(row.proof_url, { responseType: 'blob' })
    const url = URL.createObjectURL(blob)
    if (row.proof_is_image) {
      proofThumbs[row.id] = url
      lightboxUrl.value = url
      return
    }
    if (win) {
      win.location.href = url
    } else {
      window.location.href = url
    }
    setTimeout(() => URL.revokeObjectURL(url), 60000)
  } catch (error) {
    win?.close()
    paymentFormError.value = accountErrorMessage(error, 'Не удалось открыть фото')
  }
}

function onLightboxKey(event) {
  if (event.key === 'Escape') lightboxUrl.value = ''
}

async function copyShortfall() {
  const c = check.value
  if (!c?.shortfall_krw) return
  const alt = c.shortfall_display
    ? formatQuotePrice(c.shortfall_display.amount, c.shortfall_display.currency)
    : formatQuotePrice(c.shortfall_krw, 'KRW')
  const text = `Для оформления заказа не хватает ${alt}. Пожалуйста, доплатите эту сумму.`
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    window.prompt('Текст для клиента', text)
  }
}

const shareStage = computed(() => (order.value ? consultantOrderState(order.value) : 'draft'))
const shareHint = computed(() => {
  if (['draft', 'awaiting'].includes(shareStage.value)) return 'Состав, сумма к оплате и просьба прислать скриншот оплаты'
  if (shareStage.value === 'partial') return 'Состав, сколько получено и сколько доплатить'
  if (shareStage.value === 'ready') return 'Состав и подтверждение, что оплата получена'
  return 'Состав и номер заказа'
})

function withAlt(amountKrw, alt) {
  const main = formatQuotePrice(amountKrw, 'KRW')
  return alt?.amount && alt.currency !== 'KRW' ? `${main} (≈ ${formatQuotePrice(alt.amount, alt.currency)})` : main
}

function clientMessage() {
  const o = order.value
  const stage = shareStage.value
  const live = !o || dirty.value
  const rows = lines.value.map((line, index) =>
    `${index + 1}. ${line.title} — ${line.quantity} шт. × ${formatQuotePrice(line.price_krw, 'KRW')}`,
  )

  const pickup = shipping.method === 'pickup'
  const shipWhere = pickup
    ? 'самовывоз в Корее'
    : `EMS, ${countryNameFromCode(destinations.value, shipping.destination) || shipping.destination || 'страна не выбрана'}`
  const shipKrw = live ? quote.shippingKrw : o.shipping?.shipping_krw
  let shipText = 'рассчитаем после выбора страны'
  if (pickup || shipKrw === 0) shipText = 'бесплатно'
  else if (shipKrw) shipText = formatQuotePrice(shipKrw, 'KRW')

  const totalKrw = live ? previewTotalKrw.value : o.amount_krw
  const totalAlt = live
    ? { amount: previewTotalDisplay.value, currency: displayCurrency.value }
    : { amount: o.display_amount, currency: o.display_currency }
  const placed = ['exporting', 'error', 'done', 'debt'].includes(stage)
  const beforePayment = ['draft', 'awaiting'].includes(stage)

  const url = sharedCartUrl(
    window.location.origin,
    lines.value.map((line) => ({ id: line.id, quantity: line.quantity })),
    pickup ? '' : shipping.destination,
  )

  const totalLine = totalKrw != null
    ? `${beforePayment ? 'К оплате' : 'Сумма заказа'}: ${withAlt(totalKrw, totalAlt)}`
    : `Товары: ${formatQuotePrice(goodsKrw.value, 'KRW')}, итог с доставкой пришлём отдельно`

  const lead = []
  const c = check.value
  if (beforePayment) {
    lead.push(totalLine)
    if (totalKrw != null && totalAlt.amount && totalAlt.currency !== 'KRW') {
      lead.push(`Сумма в ${totalAlt.currency} — по сегодняшнему курсу.`)
    }
    lead.push('После оплаты пришлите, пожалуйста, скриншот — и мы оформим заказ.')
  } else if (stage === 'partial' && c) {
    lead.push(`Осталось доплатить: ${withAlt(c.shortfall_krw, c.shortfall_display)}.`)
    lead.push(`Получили ${formatQuotePrice(c.paid_krw, 'KRW')}, спасибо! Курс мог измениться, поэтому сумма доплаты — по сегодняшнему курсу.`)
    lead.push('Пришлите, пожалуйста, скриншот доплаты — и мы оформим заказ.')
  } else if (stage === 'ready' && c) {
    lead.push(`Оплату ${formatQuotePrice(c.paid_krw, 'KRW')} получили полностью, спасибо! Оформляем заказ.`)
  } else if (placed) {
    const number = o?.business_ru_order_number
    lead.push(number ? `Ваш заказ оформлен, номер ${number}. Спасибо!` : 'Оплата получена, заказ оформляется. Спасибо!')
    if (o?.underpaid_krw) lead.push(`Осталось доплатить: ${formatQuotePrice(o.underpaid_krw, 'KRW')}.`)
    lead.push('Сообщим, когда посылка будет отправлена.')
  }

  const greeting = `Здравствуйте${client.first_name.trim() ? `, ${client.first_name.trim()}` : ''}!`
  const details = [
    'Состав заказа:',
    ...rows,
    `Доставка (${shipWhere}): ${shipText}`,
    beforePayment ? '' : totalLine,
    url ? `Товары с фото: ${url}` : '',
  ].filter(Boolean)
  return [[greeting, ...lead].join('\n'), details.join('\n')].join('\n\n')
}

async function shareWithClient() {
  if (!lines.value.length) return
  const text = clientMessage()
  if (navigator.share && window.matchMedia('(pointer: coarse)').matches) {
    try {
      await navigator.share({ title: 'Заказ EvaCode', text })
      return
    } catch (error) {
      if (error?.name === 'AbortError') return
    }
  }
  try {
    await navigator.clipboard.writeText(text)
    notify('Текст для клиента скопирован — вставьте его в чат')
  } catch {
    window.prompt('Текст для клиента', text)
  }
}

function formatDateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function pollExport() {
  for (let i = 0; i < EXPORT_POLL_LIMIT; i += 1) {
    if (!order.value?.exporting) return
    await sleep(EXPORT_POLL_MS)
    try {
      hydrate(await auth.authFetch(`/market/consultant/orders/${order.value.id}/`))
    } catch {
      return
    }
  }
}

async function onSubmit() {
  submitError.value = ''
  if (submitting.value) return
  if (order.value?.is_draft) {
    if (!readyToSubmit.value) return
    const ok = await confirmAction({
      title: 'Оформить заказ?',
      text: 'В системе заказов EvaCode создадутся клиент, заказ, резерв и оплаты. Отменить оформление будет нельзя.',
      confirmLabel: 'Оформить',
    })
    if (!ok) return
  }
  submitting.value = true
  showHandoff({
    title: 'Оформляем заказ…',
    note: 'Создаём заказ, резерв и оплату в системе заказов EvaCode.',
    variant: 'checkout',
  })
  try {
    const data = await auth.authFetch(`/market/consultant/orders/${order.value.id}/submit/`, {
      method: 'POST',
      body: {},
    })
    hydrate(data)
    await pollExport()
    if (order.value?.business_ru_order_number && !order.value.business_ru_error) {
      notify(`Заказ оформлен: №${order.value.business_ru_order_number} в системе заказов EvaCode`)
    }
  } catch (error) {
    const data = error?.data
    if (data?.code === 'underpaid') {
      if (order.value) order.value = { ...order.value, check: data.check }
      submitError.value = 'Оплачено не полностью: курс мог измениться. Сверку обновили — запросите доплату.'
    } else {
      submitError.value = accountErrorMessage(error, 'Не удалось оформить заказ')
    }
  } finally {
    hideHandoff()
    submitting.value = false
  }
}

async function loadAll() {
  loading.value = true
  loadError.value = ''
  try {
    const apiBase = useRuntimeConfig().public.apiBase
    const [me, dest] = await Promise.all([
      auth.authFetch('/market/consultant/me/'),
      $fetch(`${apiBase}/market/shipping/destinations/`).catch(() => ({ results: [] })),
    ])
    currencies.value = me?.currencies?.length ? me.currencies : currencies.value
    destinations.value = dest?.results || []
    if (!isNew.value) {
      hydrate(await auth.authFetch(`/market/consultant/orders/${route.params.id}/`))
      if (order.value?.exporting) {
        pollExport()
      }
    } else {
      nextTick(() => {
        dirty.value = false
        addCartOnArrival()
      })
    }
  } catch (error) {
    loadError.value = accountErrorMessage(error, 'Не удалось загрузить заказ')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  window.addEventListener('keydown', onLightboxKey)
  loadAll()
})
onBeforeUnmount(() => {
  clearTimeout(goodsTimer)
  clearTimeout(quoteTimer)
  window.removeEventListener('keydown', onLightboxKey)
  Object.keys(proofThumbs).forEach(dropProofThumb)
})
</script>
