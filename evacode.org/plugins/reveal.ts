const observers = new WeakMap()

export default defineNuxtPlugin((nuxtApp) => {
    nuxtApp.vueApp.directive('reveal', {
        getSSRProps() {
            return {}
        },
        mounted(el) {
            if (import.meta.server) {
                return
            }

            const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
            if (prefersReduced || !('IntersectionObserver' in window)) {
                return
            }

            const alreadyInView = el.getBoundingClientRect().top < window.innerHeight * 0.88
            if (alreadyInView) {
                return
            }

            el.classList.add('reveal-block')

            const observer = new IntersectionObserver(
                (entries, obs) => {
                    entries.forEach((entry) => {
                        if (!entry.isIntersecting) {
                            return
                        }
                        el.classList.add('is-revealed')
                        obs.unobserve(el)
                    })
                },
                {
                    threshold: 0.15,
                    rootMargin: '0px 0px -6% 0px',
                }
            )

            observer.observe(el)
            observers.set(el, observer)
        },
        unmounted(el) {
            const observer = observers.get(el)
            observer?.disconnect()
            observers.delete(el)
        },
    })
})
