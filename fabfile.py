# -*- coding: utf-8 -*-
import sys
import json
import os
from fabric.api import cd, env, run, task, require, sudo, local
from fabric.colors import green, red, white, yellow, blue
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from fabric.operations import get
from fabric import state
from fabutils import boolean

from fabutils.env import set_env_from_json_file
from fabutils.tasks import ursync_project, ulocal, urun
import customfab

@task
def environment(env_name, debug=False):
    """
    Creates the configurations for the environment in which tasks will run.
    """
    env.env_name = env_name
    schemas_dir = "chuy/json_schemas/"
    state.output['running'] = boolean(debug)
    state.output['stdout'] = boolean(debug)
    print "Establishing environment " + blue(env_name, bold=True) + "..."
    try:
        set_env_from_json_file(
            'environments.json',
            env_name,
            schemas_dir + "environment_schema.json"
        )
        env.is_vagrant = False
        env.env_name = env_name
        env.confirm_task = True
        if env_name == "vagrant":
            result = ulocal('vagrant ssh-config | grep IdentityFile',
                            capture=True)
            env.key_filename = result.split()[1].replace('"', '')
            env.is_vagrant = True

    except ValueError:
        print red("environments.json has wrong format.", bold=True)
        sys.exit(1)

    try:
        set_env_from_json_file(
            'settings.json',
            schema_path=schemas_dir + "settings_schema.json"
        )

    except ValueError:

        print red("settings.json has wrong format.", bold=True)
        sys.exit(1)


@task
def bootstrap():
    """
    Creates the database, test information and enables rewrite.
    """
    require('dbname', 'dbuser', 'dbpassword', 'dbhost')
    confirm_task()
    print "Creating local environment."
    # Create user if environment is vagrant
    if env.env_name == "vagrant":
        run('bash cli/chuy.sh mysql_create_user {dbuser} {dbpassword}'.format(**env))
    # Creates database
    run("""
        echo "DROP DATABASE IF EXISTS {dbname}; CREATE DATABASE {dbname};
        "|mysql --batch --user={dbuser} --password=\"{dbpassword}\" --host={dbhost}
        """.format(**env))
    # Enables apache module
    run('sudo a2enmod rewrite')

    framework = ""
    while framework == "":
        print blue("Select project:")
        option  = raw_input( blue("0) Default\n1) CakePHP\n2) Symfony\n3) Laravel\n4) Drupal\n5) Prestashop\n>>") )
        if option == "0":
            framework = "default"
        if option == "1":
            framework = "cakephp"
        if option == "2":
            framework = "symfony"
        if option == "3":
            framework = "laravel"
        if option == "4":
            framework = "drupal"
        if option == "5":
            framework = "prestashop"

        env.framework = framework
        print blue("Setign vhost...")
        _set_vhost(framework)
        #Install new proyect
        option  = raw_input( blue("Install new project(Y/n)[default:n]:") )
        if option == "y" or option == "Y":
            state.output['stdout'] = True
            run('bash cli/chuy.sh {framework}_install {public_dir} {version}'.format(**env))


@task
def _set_vhost(template="cakephp"):
    """
    Set vhost
    """
    print "Update template..."

    env.template = template
    run("sudo cp /home/vagrant/templates/{template}.nginx /etc/nginx/sites-available/site".format(**env))
    run("sudo cp /home/vagrant/templates/{template}.apache /etc/apache2/sites-available/site".format(**env))
    run("sudo service nginx restart")


@task
def import_data(file_name="data.sql"):
    """
    Imports the database to given file name. database/data.sql by default.
    """
    require('dbuser', 'dbpassword', 'dbhost')
    confirm_task()

    env.file_name = file_name

    print "Importing data from file: " + blue(file_name, bold=True) + "..."
    run("""
        mysql -u {dbuser} -p'{dbpassword}' {dbname} --host={dbhost} <\
        ~/database/{file_name} """.format(**env))


@task
def export_data(file_name="data.sql", just_data=False):
    """
    Exports the database to given file name. database/data.sql by default.
    """
    require('public_dir', 'dbuser', 'dbpassword', 'dbname', 'dbhost')

    export = True

    env.file_name = file_name
    if just_data:
        env.just_data = "--no-create-info"
    else:
        env.just_data = " "

    if exists('~/database/{file_name}'.format(**env)):
        export = confirm(
            yellow(
                '~/database/{file_name} '.format(**env)
                +
                'already exists, Do you want to overwrite it?'
            )
        )

    if export:
        print "Exporting data to file: " + blue(file_name, bold=True) + "..."
        run(
            """
            mysqldump -u {dbuser} -p'{dbpassword}' {dbname} --host={dbhost}\
            {just_data} > ~/database/{file_name}
            """.format(**env)
        )
    else:
        print 'Export canceled by user'
        sys.exit(0)


@task
def resetdb():
    """
    Drops the database and recreate it.
    """
    require('dbname', 'dbuser', 'dbpassword', 'dbhost')
    confirm_task()
    print "Dropping database..."
    run("""
        echo "DROP DATABASE IF EXISTS {dbname};
        CREATE DATABASE {dbname};
        "|mysql --batch --user={dbuser} --password='{dbpassword}' --host={dbhost}
        """.format(**env))


@task
def reset_all():
    """
    Deletes all the source dir and starts over.
    """
    require('public_dir')
    confirm_task()
    print "Deleting directory content: " + blue(env.public_dir, bold=True) + "..."
    run('rm -rf {public_dir}*'.format(**env))
    run('find {public_dir} -name ".*" -delete'.format(**env))
    resetdb()


@task
def drop_all_tables():
    """
    Drops all tables from database without delete database.
    """
    require('dbname', 'dbuser', 'dbpassword', 'dbhost')
    confirm_task()
    print "Dropping tables..."
    run("""
        (echo 'SET foreign_key_checks = 0;';
        (mysqldump -u{dbuser} -p'{dbpassword}' --add-drop-table --no-data {dbname} | grep ^DROP);
        echo 'SET foreign_key_checks = 1;') | \\
        mysql --user={dbuser} --password='{dbpassword}' -b {dbname} --host={dbhost}
        """.format(**env))


@task
def sync_files(delete=False):
    """
    Sync modified files and establish necessary permissions in selected environment.
    """
    require('group', 'public_dir', 'src', 'exclude')

    print white("Uploading code to server...", bold=True)
    ursync_project(
        local_dir="'./{src}/'".format(**env),
        remote_dir=env.public_dir,
        exclude=env.exclude,
        delete=delete,
        default_opts='-chrtvzP'
    )
    print white("Estableciendo permisos...", bold=True)
    run('chgrp -R {0} {1}'.format(env.group, env.public_dir))

    print green(u'Successfully sync.')


@task
def set_webserver(webserver="nginx"):
    """
    Changes project's web server, nginx or apache2 available, nginx by default.
    """
    require('public_dir')

    if webserver == "apache2":
        sudo("service nginx stop")
        sudo("a2enmod rewrite")
        sudo("service apache2 start", pty=False)

    else:
        sudo("service apache2 stop")
        sudo("service nginx start")

    print "Web server switched to " + blue(webserver, bold=True) + "."


@task
def backup(tarball_name='backup', just_data=False):
    """
    Generates a backup copy of database
    """
    require('public_dir')

    env.tarball_name = tarball_name

    export_data(tarball_name + '.sql', just_data)

    print 'Preparing backup directory...'

    if not os.path.exists('./backup/'):
        os.makedirs('./backup/')

    if exists('{public_dir}backup/'):
        run('rm -rf {public_dir}backup/')

    if not exists('{public_dir}backup/'.format(**env)):
        run('mkdir {public_dir}backup/'.format(**env))

    if not exists('{public_dir}backup/database/'.format(**env)):
        run('mkdir {public_dir}backup/database/'.format(**env))

    run(
        'mv ~/database/{tarball_name}.sql '.format(**env)
        +
        '{public_dir}/backup/database/'.format(**env)
    )

    print 'Creating tarball...'
    with cd(env.public_dir):
        urun('tar -czf {tarball_name}.tar.gz backup/*'.format(**env))

    print 'Downloading backup...'
    download = True
    if os.path.exists('./backup/{tarball_name}.tar.gz'.format(**env)):
        download = confirm(
            yellow(
                './backup/{tarball_name}.tar.gz'.format(**env)
                +
                ' already exists, Do you want to overwrite it?'
            )
        )

    if download:
        get(
            '{public_dir}{tarball_name}.tar.gz'.format(**env),
            './backup/{tarball_name}.tar.gz'.format(**env)
        )
    else:
        print red('Backup canceled by user')

    print 'Cleaning working directory...'
    run('rm -rf {public_dir}backup/'.format(**env))
    run('rm {public_dir}{tarball_name}.tar.gz'.format(**env))

    if download:
        print green(
            'Backup succesfully created at'
            +
            ' ./backup/{tarball_name}.tar.gz'.  format(**env)
        )


@task
def execute(command=""):
    env.command = command
    state.output['stdout'] = True
    with cd('{public_dir}'.format(**env)):
        run('{command}'.format(**env))


def confirm_task(error_message = "Environment is not equals"):
    if not env.is_vagrant and env.confirm_task :
        env_name = raw_input("Confirm environment:")
        if env.env_name != env_name :
            print error_message
            sys.exit(0)
        else:
            env.confirm_task = False
