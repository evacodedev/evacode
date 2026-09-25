<template>
    <div class="evacode-slide testimonial-slide">
        <div class="customer-info">
            <div class="avatar">
                <img
                    class="customer-avatar"
                    :src="httpsMedia(testimonial.avatar)"
                    :alt="testimonial.name || 'Клиент EvaCode'"
                    width="70"
                    height="70"
                    loading="lazy"
                >
            </div>
            <div class="info">
                <div class="name">{{ testimonial.name }}</div>
                <div class="rating-stars">
                    <img
                        class="star"
                        v-for="index in testimonial.rating"
                        :key="'on-' + index"
                        src="/images/new_evacode/testimonials/testimonial-star.svg"
                        alt=""
                        width="25"
                        height="25"
                    >
                    <img
                        class="star"
                        v-for="index in 5 - testimonial.rating"
                        :key="'off-' + index"
                        src="/images/new_evacode/star-grey.svg"
                        alt=""
                        width="25"
                        height="25"
                    >
                </div>
            </div>
        </div>
        <div class="testimonial-text" v-html="testimonial.text"></div>
        <p class="testimonial-country"> {{ testimonial.country }} </p>
        <img
            v-if="testimonial.review_photo"
            class="testimonial-image"
            :src="httpsMedia(testimonial.review_photo)"
            :alt="'Фото отзыва' + (testimonial.name ? `: ${testimonial.name}` : '')"
            width="400"
            height="400"
            loading="lazy"
        >
    </div>
</template>
<script setup>
defineProps({
    testimonial: {
        type: Object,
        required: true,
    }
})
</script>
