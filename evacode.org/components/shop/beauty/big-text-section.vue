<template>
    <div>
        <section class="terms-of-use-page section-b-space">
            <div class="container">
                <img class="contact-logo" src="/images/new_evacode/evacode-contact-logo.png"  alt=""/>
                <h2 v-if="content.title" class="terms-of-use-title">{{ content.title }}</h2>
                <div class="row contacts-row section-b-space">
                    <div class="col-12">
                        <div v-if="content.description" class="terms-of-use-description" v-html="content.description">
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </div>
</template>
<script setup>

const props = defineProps({
    content: {
        type: Object,
        default: {}
    }
});

useHead({
    titleTemplate: `%s - ${props.content.title || ''}`,
    meta: [
        {
            name: 'description',
            content: `Evacode - интернет магазин корейской косметики - ${props.content.title || ''}`
        },
    ]
});
</script>
