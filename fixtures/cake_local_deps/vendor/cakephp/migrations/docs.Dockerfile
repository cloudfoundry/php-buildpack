# Generate the HTML output.
FROM markstory/cakephp-docs-builder as builder

COPY docs /data/docs

RUN cd /data/docs-builder && \
  # In the future repeat website for each version
  make website LANGS="en fr ja pt ru" SOURCE=/data/docs DEST=/data/website/2.x

# Build a small nginx container with just the static site in it.
FROM nginx:1.15-alpine

COPY --from=builder /data/website /data/website
COPY --from=builder /data/docs-builder/nginx.conf /etc/nginx/conf.d/default.conf

# Move each version into place
RUN mv /data/website/2.x/html/ /usr/share/nginx/html/2.x
