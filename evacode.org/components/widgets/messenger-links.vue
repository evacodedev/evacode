<template>
    <div class="shop-messengers" :class="'is-' + variant">
        <p v-if="heading" class="shop-messengers__title">{{ heading }}</p>
        <table class="shop-messengers__table">
            <tbody>
                <tr v-if="phone">
                    <th>
                        <i class="fa fa-phone" aria-hidden="true"></i>
                        <span>Телефон</span>
                    </th>
                    <td>
                        <a class="shop-messengers__link" :href="phoneHref">{{ phone }}</a>
                    </td>
                </tr>
                <tr>
                    <th>
                        <i class="fa fa-whatsapp" aria-hidden="true"></i>
                        <span>WhatsApp</span>
                    </th>
                    <td>
                        <a
                            v-for="item in messengers.whatsapp"
                            :key="item.href"
                            class="shop-messengers__link"
                            :href="item.href"
                            target="_blank"
                            rel="noopener noreferrer"
                        >{{ item.label }}</a>
                    </td>
                </tr>
                <tr>
                    <th>
                        <i class="fa fa-telegram" aria-hidden="true"></i>
                        <span>Telegram</span>
                    </th>
                    <td>
                        <a
                            v-for="item in messengers.telegram"
                            :key="item.href"
                            class="shop-messengers__link"
                            :href="item.href"
                            target="_blank"
                            rel="noopener noreferrer"
                        >{{ item.label }}</a>
                    </td>
                </tr>
                <tr>
                    <th>
                        <span class="shop-messengers__max" aria-hidden="true">M</span>
                        <span>Max</span>
                    </th>
                    <td>
                        <a
                            class="shop-messengers__link"
                            :href="messengers.max.href"
                            target="_blank"
                            rel="noopener noreferrer"
                        >Открыть чат</a>
                    </td>
                </tr>
                <tr v-if="email">
                    <th>
                        <i class="fa fa-envelope" aria-hidden="true"></i>
                        <span>Email</span>
                    </th>
                    <td>
                        <a class="shop-messengers__link" :href="'mailto:' + email">{{ email }}</a>
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
</template>

<script setup>
defineProps({
    variant: {
        type: String,
        default: 'stack',
    },
    heading: {
        type: String,
        default: '',
    },
    phone: {
        type: String,
        default: '',
    },
    phoneHref: {
        type: String,
        default: '',
    },
    email: {
        type: String,
        default: '',
    },
});

const messengers = useShopMessengers();
</script>
