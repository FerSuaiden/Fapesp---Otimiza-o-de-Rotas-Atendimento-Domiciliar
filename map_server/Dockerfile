FROM httpd:2.4-alpine

# Remove o index padrao do Apache e copia o site movido para map_server/site.
RUN rm -rf /usr/local/apache2/htdocs/*
COPY ./map_server/site/ /usr/local/apache2/htdocs/

# O diretorio em site/Outputs&Codigo e um symlink para fora do contexto da imagem.
# Para evitar link quebrado/403, substitui por copia real dos arquivos da raiz do repositorio.
RUN rm -rf /usr/local/apache2/htdocs/Outputs\&Codigo
COPY ./Outputs&Codigo/ /usr/local/apache2/htdocs/Outputs&Codigo/

EXPOSE 80