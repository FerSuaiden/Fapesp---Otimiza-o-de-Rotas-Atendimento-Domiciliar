FROM httpd:2.4-alpine

# Remove o index padrao do Apache e copia o site movido para map_server/site.
RUN rm -rf /usr/local/apache2/htdocs/*
COPY ./site/ /usr/local/apache2/htdocs/

# O diretorio em site/Outputs&Codigo e um symlink para fora do contexto do container.
# Para evitar 403 (Symbolic link not allowed), substitui por copia real dos arquivos.
RUN rm -rf /usr/local/apache2/htdocs/Outputs\&Codigo
COPY ./htdocs/Outputs&Codigo/ /usr/local/apache2/htdocs/Outputs&Codigo/

EXPOSE 80