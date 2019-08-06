# Generate the HTML output.
FROM markstory/cakephp-docs-builder as builder

# Copy entire repo in with .git so we can build all versions in one image.
COPY docs /data/src

RUN cd /data/docs-builder \
  && make website LANGS="en es fr ja pt ru" SOURCE=/data/src DEST=/data/website/

# Build a small nginx container with just the static site in it.
FROM nginx:1.15-alpine

COPY --from=builder /data/website /data/website
COPY --from=builder /data/docs-builder/nginx.conf /etc/nginx/conf.d/default.conf

# Move docs into place.
RUN mv /data/website/html/* /usr/share/nginx/html

# Also versioned for deployment boundary reasons
RUN ln -s /usr/share/nginx/html /usr/share/nginx/html/1.x
