#!/bin/bash

# Delete proyect
delete_proyect() {
    echo "Cleaning public dir"
    cd $public_dir
    find . -name "*" -delete
    cd ..
}

# CakePHP
# Downloads the cakephp/app (Skeleton) version specified in settings.json and installs the database.
cakephp_install() {
    public_dir=$1
    version=$2
    delete_proyect
    # Downloads Skeleton
    echo "Downloading cakephp application skeleton..."
    composer create-project --prefer-dist cakephp/app $public_dir $version
}

# Symfony
# Downloads the Symfony version specified in settings.json and installs the database.
symfony_install() {
    public_dir=$1
    version=$2
    delete_proyect
    # Downloads Symfony
    echo "Downloading Symfony..."
    composer create-project symfony/framework-standard-edition $public_dir $version
}

# Drupal
# Downloads the Drupal version specified in settings.json and installs the database.
drupal_install() {
    public_dir=$1
    version=$2
    delete_proyect
    # Downloads Drupal
    echo "Downloading Drupal..."
    cd $public_dir
    wget https://github.com/drupal/drupal/archive/$version.tar.gz
    tar -xzvf $version.tar.gz
    mv drupal-$version/* .
    rm -rf drupal-$version $version.tar.gz
}

# Prestashop
# Downloads the Prestashop version specified in settings.json and installs the database.
prestashop_install() {
    public_dir=$1
    version=$2
    delete_proyect
    # Downloads PrestaShop
    echo "Downloading PrestaShop..."
    cd $public_dir
    wget https://github.com/PrestaShop/PrestaShop/archive/$version.tar.gz
    tar -xzvf $version.tar.gz
    mv PrestaShop-$version/* .
    rm -rf PrestaShop-$version $version.tar.gz
}


# NodeJS
# Install node, grount, bower
nodejs_install() {
    sudo apt-get install python-software-properties
    sudo apt-get install software-properties-common
    sudo apt-add-repository ppa:chris-lea/node.js
    sudo apt-get update
    sudo apt-get install -y nodejs
    sudo npm install -g bower
    sudo npm -g install grunt
    sudo npm install -g grunt-cli
    sudo chown -R vagrant:vagrant /usr/lib/node_modules
    sudo chown -R vagrant:vagrant /home/vagrant/.npm
    sudo gem install compass
    sudo gem install sass
}

# call arguments verbatim:

$@
