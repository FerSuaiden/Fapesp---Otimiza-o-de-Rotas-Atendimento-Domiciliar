# Usamos a imagem oficial e leve do Apache
FROM httpd:2.4-alpine

# Copia o seu arquivo HTML para a pasta pública do Apache
# No Apache (httpd), o caminho padrão é /usr/local/apache2/htdocs/
COPY ./index.html /usr/local/apache2/htdocs/

# Expõe a porta 80 (padrão web)
EXPOSE 80