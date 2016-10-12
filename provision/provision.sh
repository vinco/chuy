#!/bin/bash

apt-get update

apt-get install python-software-properties --assume-yes
add-apt-repository ppa:ondrej/php

apt-get update


# Configurations

PACKAGES="apache2 \
  curl \
  fcgiwrap \
  git \
  mysql-client \
  mysql-server \
  nginx-full \
  spawn-fcgi \
  tree \
  vim"

PUBLIC_DIRECTORY="/home/vagrant/public_www"
DATABASE_DIRECTORY="/home/vagrant/database"

# Sets mysql pasword
debconf-set-selections <<< 'mysql-server mysql-server/root_password password password'
debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password password'

echo "Installing packages $PACKAGES ..."

apt-get install $PACKAGES --assume-yes

# Makes apache not init in start
update-rc.d -f  apache2 remove
update-rc.d php5.6-fpm defaults

# Public folder
if [ ! -d "$PUBLIC_DIRECTORY" ]; then
    mkdir $PUBLIC_DIRECTORY
fi
# database folder
if [ ! -d "$DATABASE_DIRECTORY" ]; then
    mkdir $DATABASE_DIRECTORY
fi

# Installing composer
curl -sS https://getcomposer.org/installer | php
chmod +x composer.phar
mv composer.phar /usr/local/bin/composer

# Generates unique token for application
if [ ! -f "$APP_TOKEN" ]; then
    touch $APP_TOKEN
    echo $RANDOM > $APP_TOKEN
fi
# Activates site

# Apache
cp /home/vagrant/templates/default.apache /etc/apache2/sites-available/chuy
cp /home/vagrant/templates/httpd.conf /etc/apache2/conf.d/httpd.conf
rm  /etc/apache2/sites-enabled/*
ln -s /etc/apache2/sites-available/chuy /etc/apache2/sites-enabled/
a2enmod actions
a2dissite default
a2ensite default
service apache2 stop

# Nginx
cp /home/vagrant/templates/default.nginx /etc/nginx/sites-available/chuy
cp /home/vagrant/templates/www.conf /etc/php/5.6/fpm/pool.d/www.conf
cp /home/vagrant/templates/nginx.conf /etc/nginx/nginx.conf
cp /home/vagrant/templates/nginx.conf /home/vagrant/nginx.conf
rm  /etc/nginx/sites-enabled/*
ln -s /etc/nginx/sites-available/chuy /etc/nginx/sites-enabled/
service php5.6-fpm restart
service nginx restart

# Mysql create user chuy
mysql -u"root" -p"password" -e "CREATE USER 'chuy'@'localhost' IDENTIFIED BY 'password'"
mysql -u"root" -p"password" -e "GRANT ALL PRIVILEGES ON * . * TO 'chuy'@'localhost' WITH GRANT OPTION"
