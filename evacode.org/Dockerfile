FROM node:20.19-bookworm

ENV APP_ROOT=/web

WORKDIR ${APP_ROOT}
COPY . ${APP_ROOT}

RUN npm install -g bun@1.4.0

RUN bun install

RUN bun run build
CMD ["node", ".output/server/index.mjs"]
