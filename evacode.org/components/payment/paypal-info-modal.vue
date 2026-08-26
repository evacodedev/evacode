<template>
  <div>
    <div class="modal-backdrop fade show" v-if="open"></div>

    <div
      v-if="open"
      class="modal fade show d-block bd-example-modal-md theme-modal"
      aria-hidden="true"
      tabindex="-1"
      role="dialog"
      aria-labelledby="paypalInfoModalLabel"
    >
      <div class="modal-dialog modal-md modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-body modal1">
            <div class="container-fluid p-0">
              <div class="row">
                <div class="col-12 position-relative">
                  <div class="modal-bg addtocart">
                    <button class="close btn-close" type="button" @click="closeModal">
                      <span>x</span>
                    </button>
                    <div class="media-body align-self-center text-center">
                      <h6 class="mb-3" id="paypalInfoModalLabel">Информация об оплате</h6>
                      <p>
                        Оплата с помощью международной карты и PayPal находится в стадии разработки.
                        Пока пользуйтесь обычной кнопкой "Купить"
                      </p>
                      <button class="btn-sm btn-solid" @click="closeModal">Понятно</button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  open: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['close']);

const closeModal = () => {
  emit('close');
};
</script>
