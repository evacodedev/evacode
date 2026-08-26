<template>
  <div class="back-button">
      <button
          class="evacode-btn"
          @click="backClick"
      >
          <i class="fa fa-angle-left" aria-hidden="true"></i> Назад
      </button>
  </div>
</template>

<script setup>
const backClick = () => {
    window.history.back();
}
</script>
