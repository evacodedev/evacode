// https://nuxt.com/docs/api/configuration/nuxt-config

// @ts-ignore
export default defineNuxtConfig({
    app: {
        head: {
            htmlAttrs: {
                lang: 'ru',
            },
            charset: 'utf-8',
            viewport: 'width=device-width, initial-scale=1',
            title: 'EvaCode — люксовая корейская косметика',
            meta: [
                {
                    name: 'description',
                    content: 'EvaCode — магазин люксовой корейской косметики: The History of Whoo, O HUI, SU:M37, CNP, Sulwhasoo, Hera. Офис в Корее, доставка по миру. Опт и розница. Эксклюзивный дистрибьютор CH6.',
                },
                {
                    property: 'og:title',
                    content: 'EvaCode — люксовая корейская косметика',
                },
                {
                    property: 'og:description',
                    content: 'Люксовая корейская косметика с Кореи: Whoo, O HUI, SU:M37, CNP, Sulwhasoo. Опт и розница, консультанты, доставка по миру.',
                },
                {
                    property: 'og:type',
                    content: 'website',
                },
                {
                    property: 'og:locale',
                    content: 'ru_RU',
                },
                {
                    name: 'twitter:card',
                    content: 'summary_large_image',
                },
                {
                    name: 'twitter:title',
                    content: 'EvaCode — люксовая корейская косметика',
                },
                {
                    name: 'twitter:description',
                    content: 'Люксовая корейская косметика с Кореи. Whoo, O HUI, SU:M37, CNP. Опт и розница, доставка по миру.',
                },
            ],
            link: [
                {rel: 'icon', type: 'image/png', href: '/images/evacode/favicon.ico'},
                // Lato is self-hosted (latofonts.scss). Inter only — two weights.
                {
                    rel: 'stylesheet',
                    href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap',
                },
            ],
            script:[
                {
                    src: 'https://www.googletagmanager.com/gtag/js?id=G-22XGNP36M1',
                    tagPosition: 'bodyOpen',
                },
                {
                    innerHTML:
                            `window.dataLayer = window.dataLayer || [];
                            function gtag(){dataLayer.push(arguments);}
                            gtag("js", new Date());
                            gtag("config", "G-22XGNP36M1");`,
                    tagPosition: 'bodyOpen',
                },
                {
                    type: 'text/javascript',
                    innerHTML: `
                        (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
                        m[i].l=1*new Date();k=e.createElement(t),a=e.getElementsByTagName(t)[0];
                        k.async=1;k.src=r;a.parentNode.insertBefore(k,a)})
                        (window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");
                        ym(99607281, "init", {
                            clickmap:true,
                            trackLinks:true,
                            accurateTrackBounce:true,
                            webvisor:true
                        });
                      `,
                },
            ],
            noscript: [
                {
                    children: '<div><img src="https://mc.yandex.ru/watch/99607281" style="position:absolute; left:-9999px;" alt="" /></div>',
                },
            ],
        },
    },
    runtimeConfig: {
        public: {
            apiBase: process.env.BASE_API_URL,
            url: process.env.SITE_URL || 'https://www.evacode.org',
            imgproxyPrefix: process.env.IMGPROXY_PREFIX || '',
        }
    },
    site: {
        url: process.env.SITE_URL || 'https://www.evacode.org',
        trailingSlash: true,
        name: 'EvaCode',
    },
    sitemap: {
        exclude: [
            '/account/**',
            '/page/account/cart/**',
            '/page/account/checkout/**',
            '/page/order-success/**',
            '/page/consult-success/**',
            '/page/consult/**',
            '/page/404/**',
        ],
        sources: [
            '/api/__sitemap__/urls',
        ],
        cacheMaxAgeSeconds: 600,
    },
    css: ['@/assets/scss/app.scss'],
    ssr: true,
    // Keep global CSS as a cacheable /_nuxt/*.css file instead of ~900KB inline.
    features: {
        inlineStyles: false,
    },
    experimental: {
        inlineSSRStyles: false,
    },
    modules: [
        'maz-ui/nuxt',
        'nuxt3-localforage',
        '@nuxt/image-edge',
        '@nuxtjs/robots',
        '@vueuse/nuxt',
        'nuxt-simple-sitemap',
        [
            '@pinia/nuxt',
            {
                autoImports: ['defineStore', 'acceptHMRUpdate'],
            },
        ],
    ],
    vite: {
        optimizeDeps: {
            include: ['localforage'],
        },
    },
    pluginsIgnore: [
        /^ignored-plugin/,
        /another-ignored-plugin/,
    ],
    plugins: [
        {src: './plugins/useBootstrap.client.ts', mode: 'client'},
    ]
})
