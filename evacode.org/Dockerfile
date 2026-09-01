FROM node:20.19-bookworm

ENV APP_ROOT=/web
WORKDIR ${APP_ROOT}
COPY . ${APP_ROOT}

RUN npm install -g bun@1.4.0

# Skip install scripts: old ipx/sharp would compile with node-gyp@latest and fail.
# sharp@0.35 (overrides) ships linux binaries from npm as optional packages.
RUN bun install --network-concurrency=12 --ignore-scripts

RUN bun run build
CMD ["node", ".output/server/index.mjs"]
