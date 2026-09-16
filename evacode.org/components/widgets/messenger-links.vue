<template>
    <div class="shop-messengers" :class="'is-' + variant">
        <div class="shop-messengers__group">
            <p class="shop-messengers__label">WhatsApp</p>
            <a
                v-for="item in messengers.whatsapp"
                :key="item.href"
                class="shop-messengers__link"
                :href="item.href"
                target="_blank"
                rel="noopener noreferrer"
            >{{ item.label }}</a>
        </div>
        <div class="shop-messengers__group">
            <p class="shop-messengers__label">Telegram</p>
            <a
                v-for="item in messengers.telegram"
                :key="item.href"
                class="shop-messengers__link"
                :href="item.href"
                target="_blank"
                rel="noopener noreferrer"
            >{{ item.label }}</a>
        </div>
        <div class="shop-messengers__group">
            <p class="shop-messengers__label">Max</p>
            <a
                class="shop-messengers__link"
                :href="messengers.max.href"
                target="_blank"
                rel="noopener noreferrer"
            >{{ messengers.max.label }}</a>
        </div>
    </div>
</template>

<script setup>
defineProps({
    variant: {
        type: String,
        default: 'stack',
    },
});

const messengers = useShopMessengers();
</script>
