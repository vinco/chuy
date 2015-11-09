# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|

    environments_json_path = "environments.json"
    vagrant_config = (JSON.parse(File.read(environments_json_path)))['vagrant']

    config.vm.box = "precise32"
    config.vm.box_url = "http://files.vagrantup.com/precise32.box"

    #provisioning
    config.vm.provision "shell", path: "cakephp-workflow/provision/preprovision.sh"
    config.vm.provision "file", source:"cakephp-workflow/provision/templates/", destination: "/home/vagrant/templates/"
    config.vm.provision "shell", path: "cakephp-workflow/provision/provision.sh"

    # Private IP
    config.vm.network :private_network, ip: "192.168.33.77"

    # Hosts
    config.vm.hostname = "www.cakephp-workflow.local"
    config.hostsupdater.aliases = ["cakephp-workflow.local", vagrant_config['url']]

    # Shared folders.
    config.vm.synced_folder "app", "/home/vagrant/cakephp-workflow"

    # Provider
    config.vm.provider "virtualbox" do |v|
        v.memory = 1024
        v.cpus = 2
    end

end
