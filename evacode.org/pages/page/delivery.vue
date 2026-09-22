<template>
    <Header/>
    <div class="delivery-lux">
        <section class="delivery-lux__hero">
            <img
                class="delivery-lux__hero-photo"
                src="/images/new_evacode/delivery-hero.jpg"
                alt="Студийный beauty-портрет"
                width="2400"
                height="3600"
                decoding="async"
                fetchpriority="high"
            >
            <div class="delivery-lux__hero-inner">
                <p class="delivery-lux__brand">EvaCode</p>
                <h1 class="delivery-lux__title">Доставка</h1>
                <p class="delivery-lux__lead">Отправка из Южной Кореи по миру. Возврат и отмена — по правилам ниже.</p>
            </div>
        </section>

        <section v-reveal class="delivery-lux__intro">
            <div class="container">
                <div class="delivery-lux__manifesto">
                    <p class="delivery-lux__eyebrow">Логистика</p>
                    <h2 class="delivery-lux__manifesto-title">Аккуратная упаковка и доставка до вашей страны</h2>
                    <p class="delivery-lux__manifesto-lead">
                        Выберите направление — сроки и тарифы зависят от страны и веса заказа.
                        Точную стоимость подскажет консультант при оформлении.
                    </p>
                </div>
                <ul class="delivery-lux__facts" aria-label="Ключевые факты">
                    <li class="delivery-lux__fact">
                        <span class="delivery-lux__fact-value">KR</span>
                        <span class="delivery-lux__fact-label">отправка из Кореи</span>
                    </li>
                    <li class="delivery-lux__fact">
                        <span class="delivery-lux__fact-value">7</span>
                        <span class="delivery-lux__fact-label">направлений</span>
                    </li>
                    <li class="delivery-lux__fact">
                        <span class="delivery-lux__fact-value">24ч</span>
                        <span class="delivery-lux__fact-label">на отмену заказа</span>
                    </li>
                </ul>
            </div>
        </section>

        <section v-reveal class="delivery-lux__regions">
            <div class="container">
                <p class="delivery-lux__eyebrow">Направления</p>
                <h2 class="delivery-lux__section-title">Тарифы по странам</h2>

                <p v-if="pending" class="delivery-lux__status">Загружаем условия…</p>
                <p v-else-if="!regions.length" class="delivery-lux__status">Условия доставки временно недоступны.</p>

                <template v-else>
                    <div class="delivery-lux__tabs" role="tablist" aria-label="Страны доставки">
                        <button
                            v-for="(region, index) in regions"
                            :key="region.id || index"
                            type="button"
                            role="tab"
                            class="delivery-lux__tab"
                            :class="{ 'is-active': index === activeIndex }"
                            :aria-selected="index === activeIndex"
                            @click="activeIndex = index"
                        >
                            {{ region.label }}
                        </button>
                    </div>

                    <div class="delivery-lux__country" role="tabpanel">
                        <p v-if="activeRegion?.parsed?.lead" class="delivery-lux__country-lead">
                            {{ activeRegion.parsed.lead }}
                        </p>
                        <div class="delivery-lux__methods">
                            <article
                                v-for="method in (activeRegion?.parsed?.methods || [])"
                                :key="method.title"
                                class="delivery-lux__method"
                            >
                                <h3 class="delivery-lux__method-title">{{ method.title }}</h3>
                                <ul class="delivery-lux__method-list">
                                    <li v-for="point in method.points" :key="point">{{ point }}</li>
                                </ul>
                            </article>
                        </div>
                    </div>
                </template>
            </div>
        </section>

        <section v-reveal class="delivery-lux__returns">
            <div class="container">
                <div class="delivery-lux__returns-head">
                    <p class="delivery-lux__eyebrow">Правила</p>
                    <h2 class="delivery-lux__section-title">Возврат и отмена</h2>
                    <p class="delivery-lux__returns-lead">
                        Коротко о главном. Полные условия при необходимости уточнит ваш консультант.
                    </p>
                </div>

                <ul class="delivery-lux__rule-cards">
                    <li v-for="card in returnCards" :key="card.title" class="delivery-lux__rule-card">
                        <p class="delivery-lux__rule-card-kicker">{{ card.kicker }}</p>
                        <h3 class="delivery-lux__rule-card-title">{{ card.title }}</h3>
                        <p class="delivery-lux__rule-card-text">{{ card.text }}</p>
                    </li>
                </ul>

                <div class="delivery-lux__rule-split">
                    <article v-for="block in returnChannels" :key="block.title" class="delivery-lux__rule-block">
                        <h3 class="delivery-lux__rule-block-title">{{ block.title }}</h3>
                        <p class="delivery-lux__rule-block-text">{{ block.text }}</p>
                    </article>
                </div>

                <div class="delivery-lux__rule-notes">
                    <p class="delivery-lux__rule-notes-label">Важно</p>
                    <ul>
                        <li v-for="note in returnNotes" :key="note">{{ note }}</li>
                    </ul>
                </div>

                <p class="delivery-lux__returns-help">
                    Вопросы по возврату или отмене —
                    <a href="#consult" @click.prevent="focusConsult">напишите консультанту</a>.
                </p>
            </div>
        </section>

        <section v-reveal class="delivery-lux__cta">
            <div class="container">
                <p class="delivery-lux__cta-brand">EvaCode</p>
                <h2 class="delivery-lux__cta-title">Готовы оформить заказ?</h2>
                <p class="delivery-lux__cta-text">Подберём уход и рассчитаем доставку в вашу страну.</p>
                <div class="delivery-lux__cta-actions">
                    <nuxt-link to="/collection/leftsidebar/0/" class="delivery-lux__cta-btn is-primary">В магазин</nuxt-link>
                    <nuxt-link to="/page/account/contact" class="delivery-lux__cta-btn">Контакты</nuxt-link>
                </div>
            </div>
        </section>
    </div>
    <Footer/>
</template>

<script setup>
const config = useRuntimeConfig();
const activeIndex = ref(0);

const stripEmoji = (value) =>
    String(value || '')
        .replace(/\p{Extended_Pictographic}/gu, '')
        .replace(/[\u{1F1E0}-\u{1F1FF}]/gu, '')
        .replace(/[\u{FE0F}\u{200D}]/gu, '')
        .replace(/&zwj;/gi, '')
        .replace(/\s+/g, ' ')
        .trim();

// JS \b is ASCII-only — Cyrillic titles like «Манас» need an explicit boundary.
const METHOD_TITLE_RE =
    /^(?:Any\s*Logis|EMS|SHIPKOR|ESL\s*Logis|Манас)(?=$|[\s.,:;\-—])/i;

const fixSpacing = (line) =>
    line
        .replace(/([А-Яа-яЁёA-Za-z])(\d)/g, '$1 $2')
        .replace(/(\d)([А-Яа-яЁёA-Za-z])/g, '$1 $2')
        .replace(/([А-Яа-яЁёA-Za-z])(\$)/g, '$1 $2')
        .replace(/(\$)([А-Яа-яЁёA-Za-z])/g, '$1 $2')
        .replace(/([.!?])(?=[А-ЯЁA-Z])/g, '$1 ')
        .replace(/\s+/g, ' ')
        .trim();

const htmlToLines = (html) =>
    String(html || '')
        .replace(/<br\s*\/?>/gi, '\n')
        .replace(/<\/p>/gi, '\n')
        .replace(/<\/li>/gi, '\n')
        .replace(/<li[^>]*>/gi, '\n')
        .replace(/&bull;|&#8226;|&#x2022;/gi, '\n')
        .replace(/<[^>]+>/g, ' ')
        .replace(/&nbsp;/gi, ' ')
        .replace(/&zwj;/gi, '')
        .replace(/[⭕●•·◦○◉⦿▪▫‣∙･]/gu, '\n')
        .replace(
            /(?=(?:Any\s*Logis|EMS|SHIPKOR|ESL\s*Logis|Манас)(?=$|[\s.,:;\-—]))/gi,
            '\n',
        )
        .replace(/\p{Extended_Pictographic}/gu, '')
        .replace(/[\u{1F1E0}-\u{1F1FF}\u{FE0F}\u{200D}]/gu, '')
        .split(/\n+/)
        .map((line) =>
            fixSpacing(
                line
                    .replace(/^[•·◦○\u25CF\u25CB\u2B55▪▫‣∙･]+\s*/u, '')
                    .replace(/^\d+\.\s*[.\u200B\u2060]*\s*/u, ''),
            ),
        )
        .filter((line) => line && line.length > 1 && !/^[.,!‼]+$/u.test(line));

const mergeLinkLines = (lines) => {
    const merged = [];
    let buffer = '';
    for (const line of lines) {
        if (/^[a-z0-9.-]+\.[a-z]{2,}$/i.test(line) || line === ',') {
            buffer = buffer ? `${buffer} ${line}` : line;
            continue;
        }
        if (buffer) {
            merged.push(buffer.replace(/\s+,/g, ',').replace(/,\s*$/, '').trim());
            buffer = '';
        }
        merged.push(line);
    }
    if (buffer) {
        merged.push(buffer.replace(/\s+,/g, ',').replace(/,\s*$/, '').trim());
    }
    return merged;
};

const parseRegionBody = (html) => {
    const lines = mergeLinkLines(htmlToLines(html));
    const methods = [];
    const leadLines = [];
    let current = null;

    for (const line of lines) {
        if (/способ\w*\s+доставки/i.test(line)) {
            continue;
        }
        if (METHOD_TITLE_RE.test(line)) {
            current = { title: line.replace(/\.$/, '').trim(), points: [] };
            methods.push(current);
            continue;
        }
        if (!current) {
            leadLines.push(line);
        } else {
            current.points.push(line);
        }
    }

    if (!methods.length) {
        return {
            lead: '',
            methods: leadLines.length
                ? [{ title: 'Условия', points: leadLines }]
                : [],
        };
    }

    return {
        lead: leadLines.join(' ').trim(),
        methods: methods.filter((method) => method.points.length || method.title),
    };
};

const toItem = (row) => ({
    id: row.id,
    label: stripEmoji(row.delivery_type),
    parsed: parseRegionBody(row.delivery_description),
    isReturns: /возврат|отмена/i.test(String(row.delivery_type || '')),
});

const { data: deliveryRows, pending } = await useAsyncData(
    'delivery-page-rows',
    async () => {
        try {
            const res = await $fetch(`${config.public.apiBase}/core/delivery`);
            return Array.isArray(res?.results) ? res.results : [];
        } catch (error) {
            console.error(error);
            return [];
        }
    },
    { default: () => [] },
);

const items = computed(() => (deliveryRows.value || []).map(toItem).filter((item) => item.label));
const regions = computed(() => items.value.filter((item) => !item.isReturns));
const activeRegion = computed(() => regions.value[activeIndex.value] || regions.value[0] || null);

const returnCards = [
    {
        kicker: '24 часа',
        title: 'Отмена заказа',
        text: 'Отменить заказ и вернуть оплату можно только в течение 24 часов с момента покупки.',
    },
    {
        kicker: 'Качество',
        title: 'Без возврата по желанию',
        text: 'Парфюмерно-косметические товары надлежащего качества обмену или возврату не подлежат.',
    },
    {
        kicker: 'Дефект',
        title: 'Производственный брак',
        text: 'После отправки возврат возможен только при дефекте производства: сломанная пипетка, скол на ампуле и т.п.',
    },
];

const returnChannels = [
    {
        title: 'Карго',
        text: 'При получении обязательно осмотрите посылку и составьте акт при курьере или в пункте выдачи.',
    },
    {
        title: 'EMS',
        text: 'В заказе указывается стоимость товаров. При утере EMS возмещает только указанную сумму. Доставка EMS при возврате не компенсируется.',
    },
];

const returnNotes = [
    'Товар возвращают в том же состоянии, в котором он был получен.',
    'Доставка при возврате — за счёт покупателя, кроме порчи при перевозке с актом осмотра.',
    'Возврат денег оформляется после поступления товара на склад EvaCode в надлежащем виде.',
    'Если упаковку вскрывали или тестировали продукт — деньги за него не возвращаются.',
    'При невозможности отправить товар на склад решение о возврате денег остаётся за магазином.',
    'EvaCode не отвечает за товары, возвращённые по ошибке.',
];

watch(regions, (list) => {
    if (activeIndex.value >= list.length) {
        activeIndex.value = 0;
    }
});

const focusConsult = () => {
    if (!import.meta.client) {
        return;
    }
    const el = document.getElementById('consult');
    if (!el) {
        return;
    }
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    window.setTimeout(() => {
        el.focus({ preventScroll: true });
    }, 350);
};

useHead({
    title: 'Доставка и возврат — EvaCode',
    meta: [
        {
            name: 'description',
            content: 'Доставка EvaCode из Кореи по миру: сроки, оплата, возврат и отмена заказа корейской косметики.',
        },
    ],
});
</script>
