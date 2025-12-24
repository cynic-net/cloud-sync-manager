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


Commands and Options
--------------------

Command-line completion, when added, will be available for options,
subcommands, paths and groups; paths and groups are completed from the
configuration file.

A _path_ refers to an section from the configuration file. Paths are
normalised so that e.g. `~/dir` from the configuration file can be
referenced with `/home/$USER/dir` or, if the CWD is $HOME, simply `dir/`.

A _group_ refers to all sections/paths from the configuration file that
have that string in in the `groups` list in the configuration file; the
operation will be done in turn on each member of the group. Group matching
is done before path matching, so in the example in the paragraph above, a
group `dir` will refer to the groups, not to the local `dir/` that matches
just the `~/dir` path.

### Global Options

These are available for all subcommands and are given before the
subcommand.

* `-n`/`--dry-run`: Just show what would be done, without actually
  performing the action.
* `-i`/`--interactive`: Same as rclone's interactive mode.

### Subcommands

* `csm on PATH|GROUP`: Perform the configured action for the given path or
  group (mount, sync, start periodic sync, etc.). If the path is already
  performing a configured continuous action, the path will be skipped.

* `csm off PATH|GROUP`: Disable any persistent action for the given path
  (unmount, no longer perform periodic syncs, etc.). If the path is
  configured for a continuous action that is already disabled, the path
  will be skipped.

* `csm show PATH|GROUP`: Display the name and description of the remote for
  the path, followed by a listing of the files and directories at the top
  level of that remote.

* `csm list`: List all known paths.

* `csm groups`: List all known groups and the paths associated with each.

XXX we need commands to deal with token renewal, etc. That particular one
needs to check that $DISPLAY is set (so a web browser is available), and
take an option that allows display of the URL to copy if $DISPLAY is not
set.


Configuration
-------------

Configuration is read from `~/.config/rclone/cloud-sync-manager.toml`; this
can be overridden with the `-c CONFFILE` opion.

Paths in the configuration file may start with `~/` for which the current
user's home directory will be substituted. (`~NAME` substitutions for other
users' home directories will not work.

The config file contains a section for each path, followed by key-value
pairs for the configuration. E.g.,

    ["~/cloud/foo']
    descripton = 'The foo files.'
    groups = [ 'all', 'mounts', ]
    remote = 'my-foo:'              # rclone remote `my-foo:`
    action = 'bisync'               # see actions below
    period = '5m'                   # optional; see "Periodic Actions" below

### Remotes

Remotes are given in standard [rclone] format: remote name followed by an
optional path. (This allows copying/syncing/etc. to a subdir of an rclone
remote.)

### Actions

The `action` key may have one of the following values:

* `mount`: Mount the remote on _path,_ or unmount if the `off` command is
  given.

* `bisync`: Bidirectional sync of remote with _path,_ downloading and
  uploading new and changed files and removing files that have been removed
  on the other side. (See `rclone bidir` for more information.)

* `copy-rm`: Copy all files from the remote to _path,_ overwriting any
  locally changed files and removing any files not on the remote.
  (A form of `rclone sync`.)

* `copy-keep`: Copy all files from the remote to _path,_ overwriting any
  locally changed files and keeping any local files that are not on the
  remote. (A form of `rclone copy`.)

* `copy-save`: Copy all files from the remote to _path_ but, before
  copying, move any local files that would be deleted or overwritten with
  changed data to the same path and name under `.old/` at the root of
  _path._ (XXX should this keep multiple copies of changing files, perhaps
  adding an ISO date extension?)

* `push-rm`, `push-keep`, `push-save`: As with `copy-*` except from _path_
  to the remote.

### Periodic Actions

Some actions such as copies and syncs can be repeated periodically. If a
`period` key exists in a configuration that supports it, `csm on` will
start periodic repetitions and `csm off` will stop them.

The period value is a [TOML String] which is either `'none'` (no
repetition) or an integer followed by a time unit specifier `s` seconds,
`m` minutes, or `h` hours. There is no way to mix time unites you must
specify 1.5 hours as `'90m'`. (XXX, should we change the int to a float?
Probably not because too much work to parse.)



<!-------------------------------------------------------------------->
[TOML String]: https://toml.io/en/v1.1.0#string
[rclone]: https://rclone.org/
