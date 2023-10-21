# syntax=docker/dockerfile:experimental
FROM ubuntu:20.04 as base
ARG NGINX_VERSION
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y "nginx-extras=${NGINX_VERSION}-*" lua-zlib curl && rm -rf /var/lib/apt/lists/*


FROM base as build
RUN apt-get update && \
    apt-get install -y \
        git \
        wget \
        libxml2 \
        libxslt1-dev \
        libpcre3 \
        libpcre3-dev \
        zlib1g \
        zlib1g-dev \
        openssl \
        libssl-dev \
        libtool \
        automake \
        gcc \
        g++ \
        make && \
    rm -rf /var/cache/apt

RUN wget "http://nginx.org/download/nginx-${NGINX_VERSION}.tar.gz" && \
    tar -C /usr/src -xzvf nginx-${NGINX_VERSION}.tar.gz

ARG NJS_VERSION
WORKDIR /src
RUN wget "https://codeload.github.com/nginx/njs/tar.gz/refs/tags/${NJS_VERSION}" -O "njs-${NJS_VERSION}.tar.gz" && \
    tar -C /src -xzvf njs-${NJS_VERSION}.tar.gz

WORKDIR /src/ngx_devel_kit
ARG NGX_DEVEL_KIT_COMMIT
RUN git clone https://github.com/simpl/ngx_devel_kit . && git reset --hard ${NGX_DEVEL_KIT_COMMIT}

WORKDIR /src/set-misc-nginx-module
ARG SET_MISC_NGINX_MODULE_COMMIT
RUN git clone https://github.com/openresty/set-misc-nginx-module . && git reset --hard ${SET_MISC_NGINX_MODULE_COMMIT}

WORKDIR /src/nginx-rtmp-module
ARG NGINX_RTMP_MODULE_COMMIT
RUN git clone https://github.com/arut/nginx-rtmp-module . && git reset --hard ${NGINX_RTMP_MODULE_COMMIT}

WORKDIR /usr/src/nginx-${NGINX_VERSION}
RUN NGINX_ARGS=$(nginx -V 2>&1 | sed -n -e 's/^.*arguments: //p') \
    ./configure --with-compat --with-http_ssl_module --add-dynamic-module=/src/ngx_devel_kit \
                                                     --add-dynamic-module=/src/set-misc-nginx-module \
                                                     --add-dynamic-module=/src/njs-${NJS_VERSION}/nginx \
                                                     --add-dynamic-module=/src/nginx-rtmp-module \
                                                     ${NGINX_ARGS} && make modules


FROM base as final
COPY --from=build /usr/src/nginx-${NGINX_VERSION}/objs/ngx_http_set_misc_module.so /usr/src/nginx-${NGINX_VERSION}/objs/ndk_http_module.so /usr/src/nginx-${NGINX_VERSION}/objs/ngx_http_js_module.so /usr/src/nginx-${NGINX_VERSION}/objs/ngx_rtmp_module.so /usr/lib/nginx/modules/
COPY --from=build /src/nginx-rtmp-module/stat.xsl /etc/nginx/
RUN echo "load_module modules/ngx_http_set_misc_module.so;" > /etc/nginx/modules-enabled/50-mod-http-set-misc-module.conf
RUN echo "load_module modules/ngx_http_js_module.so;" > /etc/nginx/modules-enabled/50-mod-http-js-module.conf
RUN echo "load_module modules/ngx_rtmp_module.so;" > /etc/nginx/modules-enabled/50-mod-rtmp-module.conf

RUN mkdir -p /var/cache/nginx && chown www-data:www-data /var/cache/nginx
RUN mkdir -p /var/log/nginx && ln -sf /dev/stdout /var/log/nginx/access.log && ln -sf /dev/stderr /var/log/nginx/error.log && chown -R www-data:adm /var/log/nginx

RUN mkdir -p /config

COPY config/nginx.conf config/push.conf /etc/nginx/

STOPSIGNAL SIGQUIT

ENTRYPOINT ["nginx", "-c", "/etc/nginx/nginx.conf"]

