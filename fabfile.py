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


@task
def environment(env_name, debug=False):
    """
    Creates the configurations for the environment in which tasks will run.
    """
    schemas_dir = "cakephp-workflow/json_schemas/"
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
    print "Creating local environment."
    # Creates database
    run("""
        echo "DROP DATABASE IF EXISTS {dbname}; CREATE DATABASE {dbname};
        "|mysql --batch --user={dbuser} --password=\"{dbpassword}\" --host={dbhost}
        """.format(**env))
    # Enables apache module
    run('sudo a2enmod rewrite')


@task
def cakephp_install():
    """
    Downloads the cakephp version specified in settings.json and installs the database.
    """
    require('cpworkflow_dir', 'public_dir', 'dbname', 'dbuser', 'dbpassword')

    print "Downloading cakephp application skeleton..."
    #Downloads Skeleton
    run('composer create-project --prefer-dist cakephp/app skeleton && '
        'rm -rf {public_dir}* && '
        'mv skeleton/* {public_dir} && '
        'rm -rf skeleton'.format(**env))

    print "Install cakephp version..."
    run('composer require cakephp/cakephp:"{version}" && '
        'rsync -a vendor/ {public_dir} && '
        'rm -rf vendor/'.format(**env))

#     print "Installing cakephp-workflow..."
    #Creates simbolic link to themes
    run('rm -rf {public_dir}src && '
        'rm -rf {public_dir}config  && '
        'rm -rf {public_dir}plugins  && '
        'rm -rf {public_dir}webroot  && '
        'ln -s {cpworkflow_dir}src {public_dir} '
        'ln -s {cpworkflow_dir}config {public_dir} '
        'ln -s {cpworkflow_dir}plugins {public_dir} '
        'ln -s {cpworkflow_dir}webroot {public_dir}'.format(**env))


@task
def import_data(file_name="data.sql"):
    """
    Imports the database to given file name. database/data.sql by default.
    """
    require('cpworkflow_dir', 'dbuser', 'dbpassword', 'dbhost')

    env.file_name = file_name

    print "Importing data from file: " + blue(file_name, bold=True) + "..."
    run("""
        mysql -u {dbuser} -p\"{dbpassword}\" {dbname} --host={dbhost} <\
        {cpworkflow_dir}database/{file_name} """.format(**env))


@task
def export_data(file_name="data.sql", just_data=False):
    """
    Exports the database to given file name. database/data.sql by default.
    """
    require('cpworkflow_dir', 'dbuser', 'dbpassword', 'dbname', 'dbhost')

    export = True

    env.file_name = file_name
    if just_data:
        env.just_data = "--no-create-info"
    else:
        env.just_data = " "

    if exists('{cpworkflow_dir}database/{file_name}'.format(**env)):
        export = confirm(
            yellow(
                '{cpworkflow_dir}database/{file_name} '.format(**env)
                +
                'already exists, Do you want to overwrite it?'
            )
        )

    if export:
        print "Exporting data to file: " + blue(file_name, bold=True) + "..."
        run(
            """
            mysqldump -u {dbuser} -p\"{dbpassword}\" {dbname} --host={dbhost}\
            {just_data} > {cpworkflow_dir}database/{file_name}
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
    print "Dropping database..."
    run("""
        echo "DROP DATABASE IF EXISTS {dbname};
        CREATE DATABASE {dbname};
        "|mysql --batch --user={dbuser} --password=\"{dbpassword}\" --host={dbhost}
        """.format(**env))


@task
def reset_all():
    """
    Deletes all the cakephp installation and starts over.
    """
    require('public_dir')
    print "Deleting directory content: " + blue(env.public_dir, bold=True) + "..."
    run("""rm -rf {0}*""".format(env.public_dir))
    resetdb()


@task
def sync_files():
    """
    Sync modified files and establish necessary permissions in selected environment.
    """
    require('group', 'cpworkflow_dir', 'public_dir')

    print white("Uploading code to server...", bold=True)
    ursync_project(
        local_dir='./app/',
        remote_dir=env.cpworkflow_dir,
        delete=True,
        default_opts='-chrtvzP'
    )

    print white("Estableciendo permisos...", bold=True)
    run('chmod -R o-rwx {0}'.format(env.cpworkflow_dir))
    run('chmod -R o-rwx {0}'.format(env.public_dir))
    run('chgrp -R {0} {1}'.format(env.group, env.cpworkflow_dir))
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
        with open('cakephp-workflow/defaults/htaccess') as htaccess:
            urun(" echo '{0}' > {1}.htaccess".
                 format(htaccess.read(), env.public_dir))

        sudo("service apache2 start", pty=False)

    else:
        sudo("service apache2 stop")
        if exists("{0}.htaccess".format(env.public_dir)):
            urun("rm {0}.htaccess".format(env.public_dir))
        sudo("service nginx start")

    print "Web server switched to " + blue(webserver, bold=True) + "."


@task
def backup(tarball_name='backup', just_data=False):
    """
    Generates a backup copy of database
    """
    require('cpworkflow_dir', 'public_dir')

    env.tarball_name = tarball_name

    export_data(tarball_name + '.sql', just_data)

    print 'Preparing backup directory...'

    if not os.path.exists('./backup/'):
        os.makedirs('./backup/')

    if exists('{cpworkflow_dir}backup/'):
        run('rm -rf {cpworkflow}backup/')

    if not exists('{cpworkflow_dir}backup/'.format(**env)):
        run('mkdir {cpworkflow_dir}backup/'.format(**env))

    if not exists('{cpworkflow_dir}backup/database/'.format(**env)):
        run('mkdir {cpworkflow_dir}backup/database/'.format(**env))

    run(
        'mv {cpworkflow_dir}/database/{tarball_name}.sql '.format(**env)
        +
        '{cpworkflow_dir}/backup/database/'.format(**env)
    )

    print 'Creating tarball...'
    with cd(env.cpworkflow_dir):
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
            '{cpworkflow_dir}{tarball_name}.tar.gz'.format(**env),
            './backup/{tarball_name}.tar.gz'.format(**env)
        )
    else:
        print red('Backup canceled by user')

    print 'Cleaning working directory...'
    run('rm -rf {cpworkflow_dir}backup/'.format(**env))
    run('rm {cpworkflow_dir}{tarball_name}.tar.gz'.format(**env))

    if download:
        print green(
            'Backup succesfully created at'
            +
            ' ./backup/{tarball_name}.tar.gz'.  format(**env)
        )
