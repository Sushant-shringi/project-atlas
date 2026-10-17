FROM php:8.1-apache

# Install required system tools and PHP extensions
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    tar \
    libcurl4-openssl-dev \
    && docker-php-ext-install curl mysqli pdo pdo_mysql \
    && a2enmod rewrite \
    && rm -rf /var/lib/apt/lists/*

# Download official CodeIgniter 3.1.13 system core
WORKDIR /var/www/html
RUN curl -sSL https://github.com/bcit-ci/CodeIgniter/archive/refs/tags/3.1.13.tar.gz -o ci3.tar.gz \
    && tar -xzf ci3.tar.gz \
    && cp -r CodeIgniter-3.1.13/system /var/www/html/system \
    && rm -rf CodeIgniter-3.1.13 ci3.tar.gz

# Copy custom CodeIgniter 3 application files
COPY . /var/www/html/

# Ensure appropriate permissions for web server
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html

EXPOSE 80
CMD ["apache2-foreground"]
