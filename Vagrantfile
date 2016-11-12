# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

    environments_json_path = "environments.json"
    vagrant_config = (JSON.parse(File.read(environments_json_path)))['vagrant']

    settings_json_path = "settings.json"
    vagrant_settings = (JSON.parse(File.read(settings_json_path)))

    config.vm.box = "ubuntu/trusty64"

    #provisioning
    config.vm.provision "shell", path: "chuy/provision/preprovision.sh"
    config.vm.provision "file", source:"chuy/provision/templates/", destination: "/home/vagrant/templates/"
    config.vm.provision "file", source:"chuy/cli/", destination: "/home/vagrant/cli/"
    config.vm.provision "shell", path: "chuy/provision/provision.sh"

    # Private IP
    config.vm.network :private_network, ip: "192.168.33.77"

    # Hosts
    config.vm.hostname = "www.chuy.local"
    config.hostsupdater.aliases = ["chuy.local", vagrant_config['url']]

    # Shared folders.
    config.vm.synced_folder vagrant_settings['src'], "/home/vagrant/public_www", id: "vagrant-root",
        owner: "vagrant",
        group: "www-data",
        mount_options: ["dmode=775,fmode=764"]

    config.vm.synced_folder "database", "/home/vagrant/database", id: "vagrant-jefecito"

    # Provider
    config.vm.provider "virtualbox" do |v|
        v.memory = 1024
        v.cpus = 2
    end

    # Triggers
    config.trigger.after :up do
        print File.read("chuy/logo")
    end

end
