FROM node:20.19-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        pkg-config \
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

# Do not set SHARP_IGNORE_GLOBAL_LIBVIPS — even "0" is truthy and forces a download.
RUN pkg-config --modversion vips-cpp

RUN bun install --network-concurrency=12

RUN bun run build
CMD ["node", ".output/server/index.mjs"]
