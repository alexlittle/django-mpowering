==================================
COVID-19 Library Content Platform
==================================

Development
===========

To simplify development including creating migrations and running the
devserver, the bundled `manage.py` file can be used with the settings and
configuration in the `config` module.::

    ./manage.py makemigrations orb
    ./manage.py migrate
    ./manage.py runserver

Configuration
-------------

All custom settings should be placed in `config/local_settings.py`. This file
is not source controlled. It should be written in the same format as any other
Django settings file. The primary settings file will try a naked import from
this file at the end of the main settings file, overriding any other settings
specified and adding any new ones.

The settings included are designed to be as simple and sensible for baseline
development as possible. It is *highly* recommended that the local settings
file be used to specify database settings.

Docker containers
-----------------

The Docker container system is *mostly* there, and at this point allows basic
use and development using Docker Compose (using version 2 config).

With Docker and Docker Compose installed, add this line to the `.env` file in
your project root (adding it if absent):

    COMPOSE_FILE=dev.yml

Add any seed data in the form of a SQL dump to `local_data/mysql-init/`. All SQL
files found here will be executed when the container is *first* created.

Then run:

    docker-compose up

This will bring up three containers:

1. MySQL
2. Solr
3. Django application

The Solr container will be up but for reasons of configuration to be completed
is not a working search backend yet.

To shutdown the containers run:

    docker-compose down

If the Django application is unresponsive because of a missing database then run:

    docker-compose restart django

It may be the case that the container finished loading before the MySQL container
and service were available.

To run a Django command, use the following:

    docker-compose run django python manage.py <command>

Testing
=======

The tests for the COVID-19 Library platform can be run using the current Python path (or
currently activated virtual environment) using the command::

    make test-django

The project is also configured to use `tox
<http://tox.readthedocs.org/en/latest/>`_ for isolated testing and test
environment matrices. This ensures that the full test environment can be
created *outside* and apart from the development environment and that tests can
be run against the application with different dependency versions, including
Django and even different Python versions. To use tox first install it::

    pip install tox

And then run the command::

    tox

Using the `-r` flag will recreate the test environment from scratch.::

    tox -r
    tox -e py36-django2.2 -r

For running a large matrix of tests, consider using the `detox
<https://pypi.python.org/pypi/detox>`_ tool which parallelizes tests based on
the number of available cores.::

    pip install detox
    detox

Environments
------------

The `flake8` environment is limited to running `flake8` for linting and basic
static analysis.

The `deployed` environment uses the frozen requirements file to ensure that
every dependency is pinned to the same requirements used to deploy the
application. (Note that this still requires settings updates to ensure that the
same database backend is used.)

The remaining environments are designed to work around different versions of
Django, to allow testing against future Django versions. The requirements here
should be loose enough to allow newer versions of the dependency to be used.


JS Development / Test Running (VueJS)
-------------------------------------

All JS-based application development based on VueJS is done in the local `vue` directory.
On initial environment, run `make vue-deps`. This will download the needed 
node and js files to the local `vue` directory.

Vue and its dependencies are bundled with the application JS file, `course-builder.js`. This
is done so that all JS downloads at one time and is cached, so that if a user goes offline, 
they will not need to download the files again.

The following commands are useful for development:

`make vue-deps`: install vue and node dependencies
`make vue-test`: run the vue unit tests once
`make vue-test-dev`: run the vue unit tests in watch mode for TDD
`make vue-dev`: run the webpack vue builder for development in browser, file are watched
'make vue-build`: run the webpack build to minimize and select correct vue files for production
