FROM node:20.19-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libvips42 \
        libvips-dev \
        python3 \
        make \
        g++ \
    && rm -rf /var/lib/apt/lists/*

ENV APP_ROOT=/web
WORKDIR ${APP_ROOT}
COPY . ${APP_ROOT}

RUN npm install -g bun@1.4.0

# Old sharp from @nuxt/image-edge/ipx tries GitHub for libvips and times out on the VPS.
# Use Debian libvips when it fits; otherwise pull binaries from the npm mirror.
ENV SHARP_IGNORE_GLOBAL_LIBVIPS=0
ENV SHARP_LIBVIPS_BINARY_HOST=https://cdn.npmmirror.com/binaries/sharp-libvips
ENV npm_config_sharp_libvips_binary_host=https://cdn.npmmirror.com/binaries/sharp-libvips

RUN bun install --network-concurrency=12

RUN bun run build
CMD ["node", ".output/server/index.mjs"]
