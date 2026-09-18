<template>
    <div id="consult" class="consulting" tabindex="-1">
        <div class="container">
            <section class="small-section border-section border-top-0">
                <div class="row">
                    <div class="col-lg-6">
                        <img
                            class="consult-girl"
                            src="/images/new_evacode/consult/consult-girl.jpg"
                            alt="Консультант поможет подобрать уход"
                            width="900"
                            height="1125"
                        >
                    </div>
                    <div class="col-lg-6 consult-column">
                        <h2 class="request-tg-consult">Запросите консультацию!</h2>
                        <h4>Получите персональный подбор косметического ухода от наших консультантов</h4>
                        <WidgetsMessengerLinks
                            variant="consult"
                            phone="+8210-7652-8595"
                            phone-href="tel:+821076528595"
                            email="sales@evacode.org"
                        />
                    </div>
                </div>
            </section>
        </div>
    </div>
</template>

<style scoped>
.consult-girl {
    display: block;
}

.consulting {
    scroll-margin-top: 120px;
}

.consulting:focus {
    outline: none;
}

.consulting:focus-visible {
    outline: 2px solid #b89254;
    outline-offset: 4px;
}
</style>
