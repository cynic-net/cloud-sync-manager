cloud-sync-manager
==================

cloud-sync-manager, run as `csm`, is a wrapper around [rclone] to help
manage configurations of rclone remotes and local directories. The
configuration is in two parts:

1. The standard rclone configuration file continues to handle cloud storage
   connectivity and authentication information. This is usually unique to
   every host as each host will be using different authentication tokens.

2. A csm configuration file contains mappings of rclone remotes to local
   directories and information on how to process these (mount, sync, copy,
   etc.) This is usually common to all hosts for a particular user.



<!-------------------------------------------------------------------->
[rclone]: https://rclone.org/
