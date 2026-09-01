// https://nuxt.com/docs/api/configuration/nuxt-config

// @ts-ignore
export default defineNuxtConfig({
    app: {
        head: {
            charset: 'utf-8',
            viewport: 'width=device-width, initial-scale=1',
            title: 'Evacode - интернет магазин корейской косметики',
            meta: [
                {
                    name: 'description',
                    content: 'Evacode - интернет магазин корейской косметики.- The History of Whoo, O HUI, SU:M37,' +
                        'CNP, The Saga of Soo, Sulwhasoo, Hera, Amore Pacifi'
                },
                {
                    name: 'og:description',
                    content: 'Evacode - интернет магазин корейской косметики.- The History of Whoo, O HUI, SU:M37,' +
                        'CNP, The Saga of Soo, Sulwhasoo, Hera, Amore Pacifi'
                },
                {
                    name: 'twitter:description',
                    content: 'Evacode - интернет магазин корейской косметики.- The History of Whoo, O HUI, SU:M37,' +
                        'CNP, The Saga of Soo, Sulwhasoo, Hera, Amore Pacifi'
                },
                {
                    name: 'og:title',
                    content: 'Evacode - интернет магазин корейской косметики'
                },
            ],
            link: [
                {rel: 'icon', type: 'image/png', href: '/images/evacode/favicon.ico'},
                {rel: 'stylesheet',  href: 'https://fonts.googleapis.com/css2?family=Rubik:wght@100;200;300;400;700;900&display=swap'},
                {rel: 'stylesheet',  href: 'https://fonts.googleapis.com/css2?family=Lato:wght@100;200;300;400;700;900&display=swap'},
                {rel: 'stylesheet',  href: 'https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;700;900&display=swap'}
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
            url: process.env.SITE_URL,
        }
    },
    site: {
        url: process.env.SITE_URL,
        trailingSlash: true,
    },
    css: ['@/assets/scss/app.scss'],
    ssr: true,
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
