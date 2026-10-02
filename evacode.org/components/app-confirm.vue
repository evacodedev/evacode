<template>
  <Teleport to="body">
    <div
      v-if="confirmState.open"
      class="app-confirm"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="app-confirm-title"
      :aria-describedby="confirmState.text ? 'app-confirm-text' : undefined"
      @click.self="settleConfirm(false)"
      @keydown.esc="settleConfirm(false)"
    >
      <div class="app-confirm__card">
        <p id="app-confirm-title" class="app-confirm__title">{{ confirmState.title }}</p>
        <p v-if="confirmState.text" id="app-confirm-text" class="app-confirm__text">{{ confirmState.text }}</p>
        <div class="app-confirm__actions">
          <button ref="cancelButton" type="button" class="consultant-btn consultant-btn--ghost" @click="settleConfirm(false)">
            {{ confirmState.cancelLabel }}
          </button>
          <button
            type="button"
            class="consultant-btn consultant-btn--primary"
            :class="{ 'is-danger': confirmState.danger }"
            @click="settleConfirm(true)"
          >
            {{ confirmState.confirmLabel }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
const { confirmState, settleConfirm } = useAppNotice()
const cancelButton = ref(null)

watch(
  () => confirmState.value.open,
  (isOpen) => {
    if (isOpen) nextTick(() => cancelButton.value?.focus())
  },
)
</script>
