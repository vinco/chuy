# Chuy

PHP Workflow project

## Requirements

+ [Vagrant](http://www.vagrantup.com/)
+ [Vagrant hostsupdater](https://github.com/cogitatio/vagrant-hostsupdater)
+ [Vagrant triggers](https://github.com/emyl/vagrant-triggers)
+ [Python](http://www.python.org/)
+ [Fabric](http://www.fabfile.org/)
+ [fabutils](https://github.com/vinco/fabutils)

## Support frameworks
+ Cakephp 3
+ Symfony
+ Laravel
+ Drupal

## Setup

1. Create a directory wich will contain your wordpress project

    ```bash
    $ mkdir my-new-project
    $ cd my-new-project
    ```

2. Init your repository

    ```bash
    $ git init
    ```

3. Clone this repo in your project's root directory

    ```bash
    $ git submodule add https://github.com/vinco/chuy.git
    ```

4. Run the `startProject.sh` script to create the WordPress Workflow scaffolding

    ```bash
    $ chuy/startProject.sh
    ```

## Workflow

After runing the setup, the default structure in your root directory will be as follows:

```bash
 .
 ├── environments.json
 ├── settings.json
 ├── fabfile.py
 ├── app
 │   ├── database
 └── Vagrantfile
```

### environments.json

This file contains the description of the environments where your project will
be running. By default, it is populated with the `vagrant` environment that
defines all the required paramaters to interact with the development Vagrant VM.

You must append the definition of your live devel, staging, production and any
environment that you require.

```json
# environments.json
{
    "vagrant": {
        "...": "..."
    },
    "devel": {
        "user": "my-user",
        "group": "www-data",
        "hosts": ["my-host.com"],
        "site_dir": "/srv/www/my-site.com/public/",
        "cpchuy_dir": "/srv/www/my-site.com/workflow/",
        "command_prefixes": [
            "/srv/www/my-site-com/env/activate"
        ]
    }
}
```

Note that:

+ You must define a user, group and an array of hosts for your environment.
+ Every directory path must end with a slash (/).
+ You can define an array of command prefixes that should be activated before a
  command is run in an environment. You must only list the path to your prefix scripts.

To run a task in an environment you must call the facbric's `environment` task
specifying with a colon the name of the environment.

```bash
# To run a task in the Vagrant VM
$ fab environment:vagrant ...

# To run a task in the statging environment
$ fab environment:devel ...
```


### settings.json

This file contains the general project configuration, you need to set it before
installing PHP framework or running the fabric commands.

```json
{
    "src": "app"
    "version": "3.1.1",
    "locale": "es_ES",
}

```

Now you can install PHP framework on your vagrant machine by running the following command:

```
$ fab environment:vagrant bootstrap
```

This will Create the database, install the version of PHP framework you specified.
If you get any errors durring the setup processes you will have to fix the error and then run "$ fab vagrant reset_all" which will clean up the failed installation and automatically re-run bootstrap.


### fabfile.py

This file contains the core functionality of chuy, it has tasks that can be
executed both in vagrant virtual machine as well as in the server (Q.A., Dev, Production)
these tasks need to be executed in the general form:

```bash
$ fab environment:name task1 task2 ... task3
```

For example if you want to sync files to devel  the command would be

```bash
$ fab environment:devel sync_files
```

Available commands:
```
backup          Generates a backup copy of database
bootstrap       Creates the database, test information and enables rewrite.
environment     Creates the configurations for the environment in which tasks will run.
execute
export_data     Exports the database to given file name. database/data.sql by default.
import_data     Imports the database to given file name. database/data.sql by default.
nodejs_install  Install node, grount, bower
reset_all       Deletes all the cakephp installation and starts over.
resetdb         Drops the database and recreate it.
set_webserver   Changes project's web server, nginx or apache2 available, nginx by default.
sync_files      Sync modified files and establish necessary permissions in selected environment.
```

You can list the available enviroments and task by running ``fab --list``


### Directories

All of your development should be placed in the src/ directories:

src/database: All .sql files should be placed here


## Access

You can now browse to http://chuy.local where you can find you installation of wordpress.
