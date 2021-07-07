====================
Library Peer Network
====================

:synopsis: Shared data across a network of peers

The COVID-19 Library API allows for accessing resource information programmatically.
This allows for one COVID-19 Library instance to download resources from another, syncing
resources across a network of COVID-19 Library peers. This allows critical health data to
be shared and reused without tedious manual updates.

The starting requirement is API access to the target COVID-19 Library (e.g. the global Last Mile Health COVID-19 Library).

Setting up peers
================

A peer is added to your COVID-19 Library instance by adding four data items:

- peer name (identifying)
- host name (web address)
- user name
- API key

Obtaining credentials
---------------------

1. Log into the target system from which you would like to sync resources, e.g. https://covid-19library.org/
2. Find and click on the "Edit Profile" link from the "My COVID-19 Library" menu
3. Copy your API key from the bottom of the form

.. figure:: /images/profile-menu.png
   :alt: Profile menu

   The Edit Profile link in the user menu.

.. figure:: /images/profile-api-key.png
   :alt: Profile API key

   Your API cannot be edited but can be copied from the form.

Configuring the peer
--------------------

New peers can be added from the Django admin (https://your-host-name/admin/) or using the
management command, `add_peer`, from the command line.

From the Django admin interface, scroll down to the "Peers" menu and then you can
directly click the "Add" link.

.. figure:: /images/peer-admin-menu.png
   :alt: Peers menu in admin

   The Peers admin group is available by scrolling down.

Then in the Add Peer form, enter the required information.

1. A name for this peer which will be used for you to identify the peer
2. The host name should include the https:// prefix
3. The username on the target peer
4. The API key for that user on the target peer

.. figure:: /images/peer-admin-setup.png
   :alt: Adding a peer form

   The Add Peer form showing the fields.

The "Active" checkbox will be checked by default and should be left checked
for as long as you want this peer to be included in any resource syncing
actions.

.. CAUTION::
    Note that the API key is stored and read in plaintext.

How syncing works
=================

The core action of the peer data sync is to **copy or update resources** from the remote
COVID-19 Library to the local COVID-19 Library.

Resoures are globally identified
--------------------------------

Every resource (along with associated files, links, and tags) has a *globally unique identifier* which is copied with synced resource.
This ensures that a resource can be downloaded from one COVID-19 Library and from yet another and
still retain a non-overridable ID that tracks it across instances. This GUID is used to
identify resources for update. It also ensures that the resources you have created for
your own library are never modified by the syncing process.

New synced resources
--------------------

Resources on the remote COVID-19 Library that are not present on the local COVID-19 Library are copied to new
resources in the local COVID-19 Library and placed in the pending state. These must be reviewed
by a content administrator prior to becoming public on the local COVID-19 Library.

Synced resources get updates
----------------------------

If you have added a synced resource from another peer and that peer later makes
updates to that resource then those updates will overwrite any local changes you have
made to that resource the next time you sync that peer's resources.

Files are not synced
--------------------

When resources have one or more files associated with them for download, these files
are not synced with the resource information. The file information is maintained as
a link to the file on the original source system.

Syncing data
=============

To sync data from a configured COVID-19 Library peer, use the `sync_peer_resources` management
command. This can be used without arguments or the numeric primary keys of configured
peers can be provided to sync only from select peers.

The syncing action makes a log of each time it runs for each peer, and uses this log to add
a time-based filter for retrieving resources from the target peer. This means that the first
time it will look at all approved resources, and on subsquent runs it will only ask for approved
resources that were updated *after* the last syncing action for that peer was run.

The primary keys can be discovered via the Django admin or by using the management
command `list_peers`.

Serving as a peer
=================

There are no additional steps required in order for your instance of the COVID-19 Library
to serve as a peer. Users with valid API keys for your instance can sync shared content
from your library. This has no effect on the state of content in your hosted instance.

