FROM httpd:2.4-alpine

# Remove o index padrao do Apache e copia o site movido para map_server/site.
RUN rm -rf /usr/local/apache2/htdocs/*
COPY ./site/ /usr/local/apache2/htdocs/

EXPOSE 80