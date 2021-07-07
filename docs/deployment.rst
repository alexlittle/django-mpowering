==============
AWS Deployment
==============

The Covid Library can be deployed as a cloned instance by using
the open source Django project with any deployment strategy or
by starting with a pre-packaged community machine image (AMI) for
running on Amazon Web Services.

Quickstart deployment to AWS
============================

The codebase includes a CloudFormation template, `cloudformation.yml`,
which can be uploaded as-is to the AWS CloudFormation service and
used to create an entire stack including EC2 instance, VPC, security
groups, and internet gateway.

1. Log into your AWS console
2. Access the CloudFormation console: https://console.aws.amazon.com/cloudformation/home
3. Click the "Create stack" button and then select "With new resources"
4. Ensure "Template is ready" is selected and then choose "Upload a template file"
5. Find the `cloudformation.yml` file on your computer and select it
6. Follow the subsequent dialog forms and then wait for your stack to finalize.

You will need to select a keypair to install for access. The remaining
items can be completed manually or in some cases with some help from
the Ansible tasks herein.

.. important::
   The Ansible tasks assume you have configured a host named `covid-library`
   (e.g. in `/ssh/config` on Linux or macOS) that specifies the host address,
   username (`ubuntu`), and path to the identify file you used to create
   your stack. You may reconfigure this as you want, but in order to work out
   of the box it is recommend you start by configuring a named `covid-library`
   host.

In the "Outputs" tab of the completed CloudFormation stack you can find the
IP address to your instance.

Direct AMI initialization
=========================

If you already have your own VPC established you can simply start an instance
from the Amazon EC2 AMI, which has ID of `ami-0c090dc979740a94b`.

Updating your installation
==========================

Prerequisites:

1. You have a recent version of Ansible installed.
2. Your instance is already installed remotely and accessible over SSH.
3. You have a remote SSH host configured with the name "covid-library" with
   host name, user, and identify file preconfigured. This is not strictly
   required however without it you will need to adapt the hosts information.

Installation Steps
------------------

These steps will complete installation so your site is available over HTTPS
and your custom domain.

1. Add a `custom.yml` file in `deployment/vars`. This is where you will
   keep custom variables, e.g. the host name of your site.
2. Run the `aws.sh` script with the extra flag `--check` - this will be passed
   through to the Ansible playbook program and ensures that it runs without
   doing anything at first, just showing what it *would* do if it ran
3. Now run the script without the `--check` flag.

If this ran successfully your site should now be accessible over HTTPS from your
custom domain.

Creating your user
------------------

To add your own accessible user, run the `add_super_user` management command.
This command can be called with two flag based arguments, `--email` and `--password`,
to create a new user with the `email` arg as both email and username, and setting
the given password.

You can call this without arguments and it will run the built-in Django
`createsuperuser` command, prompting you for username, email, and confirmed
password, and then creating the initial UserProfile. This requires slightly
more information but is marginally more secure.

Subsequent updates and working with the deployment
==================================================

The root of the deployed directory is `/home/www/platform`. Unless you change your `~/.bashrc`
file, this will be your working directory when you log into the instance. You will
also have the library's Python 3.6 virtual environment activated immediately. This
has the effect of changing the Python path and aligning it with the web application's
isolated virtualenvironment.

To access the Django app, change into `django-covid`.

    cd django-covid

The first thing you should assess and modify is the `local_settings.py` file which is
located in `config/local_settings.py`, the full path is `/home/www/platform/django-covid/config/local_settings.py`.
This file is not source controlled and is *imported* by the Django application's primary
source controlled settings. By doing so it may override the base settings or add to them.

You should go through this file and address the items commented for your attention, including
the Django "secret key" (you can change to arbitrarily random text), various email addresses,
and the allowed host names.

Deploying to an existing server
===============================

The Covid Library application can be deployed to an existing server or using a
custom configuration. The AMI ships with the following software versions,
and while other versions will likely work just as well, they have not been
tested.

- Ubuntu 16.04 LTS
- Apache 2.4
- Python 3.6
- libapache2-mod-wsgi-py3 4.3
- MySQL 5.7
- Solr 4.10

The only hard requirement for custom deployments is that you use Python 3.6.

Alternative combinations could use `Gunicorn <https://gunicorn.org/>`_ proxied behind
`Nginx <https://nginx.org/>`_, use PostgreSQL (not tested, but there are no MySQL
specific features used by the library), and use a different Solr version or search
engine altogether. The latter may be appealing given that the version of Solr here
is not current, however changing the Solr version or search engine would require
changes to the search engine index templates.

At a high level, the outline of the steps for installing and running on a separate
server would look like the following:

1. Establish an application project directory
2. In this directory clone the project Git repository into `django-covid`
3. Create a Python virtual environment named `env` here, `python3.6 -m virtualenv env --python=$(which python3.6)`
   (specifying the Python path using the `--path` option ensures the correct Python version for the environment)
4. Active the virtual environment and install the requirements (`source env/bin/activate && cd django-covid && pip install -r requirements.txt`)
5. Add a local settings file in `django-covid/config/local_settings.py` and use this to override
   project specific settings such as `DATABASES`, `SECRET_KEY`, etc. A sample can be found in
   the `deployment/` directory. You will need to set up media and static file directories,
   respectively, and ensure that your application's system user has read and write access to these
   directories and that they are mapped in your webserver host configuration (again, refer to
   the included Ansible Apache host templates here).
6. Either install `mod_wsgi` and enable in Apache and follow the WSGI settings in the Ansible
   templates here OR set up a different application server. If you are using Nginx then Gunicorn
   or `uWSGI <https://uwsgi-docs.readthedocs.io/en/latest/>`_ are good choices for serving the
   Django application. Setting these up is beyond the scope of these docs.
7. You will need to migrate your database using the `python manage.py migrate` command from the
   application root (i.e. the cloned repository) and collect static files from various installed
   Django apps (e.g. the core `orb` installation itself, the Django admin app, etc) into your
   configured static files directory (`python manage.py collectstatic --noinput`)


