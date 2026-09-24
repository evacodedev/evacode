FROM nginx

RUN rm /etc/nginx/conf.d/default.conf \
    && mkdir -p /var/cache/nginx/imgproxy \
    && chown -R nginx:nginx /var/cache/nginx/imgproxy
COPY nginx.conf /etc/nginx/conf.d
# COPY frontend /www/data
WORKDIR /www/data