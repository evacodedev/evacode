<template>
    <div class="evacode-slide testimonial-slide">
        <div class="customer-info">
            <div class="avatar">
                <img class="customer-avatar" :src="testimonial.avatar" alt="">
            </div>
            <div class="info">
                <div class="name">{{ testimonial.name }}</div>
                <div class="rating-stars">
                    <img class="star" v-for="index in testimonial.rating" src="/images/new_evacode/testimonials/testimonial-star.svg">
                    <img class="star" v-for="index in 5 - testimonial.rating" src="/images/new_evacode/star-grey.svg">
                </div>
            </div>
        </div>
        <div class="testimonial-text" v-html="testimonial.text"></div>
        <p class="testimonial-country"> {{ testimonial.country }} </p>
        <img class="testimonial-image" :src="testimonial.review_photo">
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
