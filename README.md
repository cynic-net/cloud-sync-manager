cloud-sync-manager
==================

> [!NOTE]
> A † symbol identifies features that are not yet implemented.

cloud-sync-manager (CSM), run as `csm`, is a wrapper around [rclone] to
help manage configurations of rclone remotes and local directories. The
configuration is in two parts:

1. The standard rclone configuration file continues to handle cloud storage
   connectivity and authentication information. This is usually slightly
   different on every PC as each PC will be using different authentication
   tokens.

2. A CSM configuration file contains mappings of rclone remotes to local
   directories and information on how to process these (mount, sync, copy,
   etc.) This can be common to all PCs used by a particular user.


Commands and Options
--------------------

Command-line completion† (when added) will be available for options,
subcommands, paths and groups; paths and groups are completed from the
configuration file.

A _path_ refers to an section from the configuration file. All paths in the
configuration file must be absolute; starting a path with `~/` is
considered absolute as it's normalised to `/home/$USER/dir` or similar.
Absolute and relative paths given on the command line are also normalised
assuming a `~/dir` in the configuration file, you may reference it with:
`/home/$USER/dir`; `/home/../home/$USER/dir`; - `dir/` when CWD=`$HOME`;
`./` when CWD=`$HOME/dir`; `..` when CWD=`$HOME/dir/foo`; etc.

A _group_ refers to all sections/paths from the configuration file that
have that string in in the `groups` list in the configuration file; the
operation will be done in turn on each member of the group, just as it
would be if the paths were listed explicitly on the command line. Group
matching is done before path matching, so in the example in the paragraph
above, a group `dir` will refer to the groups, not to the local `dir/` that
matches just the `~/dir` path.

For commands that take one or more paths and/or groups, generally
providing zero is fine; the command will successfully do nothing.

### Global Options

These are available for all subcommands and are given before the
subcommand.

* `-n`/`--dry-run`: Just show what would be done, without actually
  performing the action.

* `-i`/`--interactive`: Enables rclone's [interactive] mode, requesting
  manual confirmation before destructive operations..

* `-v`/`--verbose`: Enable verbose output describing what CSM is doing.

* `-p`/`--progress`: Have rclone show progress of transfers (continuous
  updates of time, files checked and amount transferred). This is useful on
  interactive terminals only.

### Subcommands

* `csm on GROUP|PATH  …`: Perform the configured action (mount, sync, start
  periodic sync, etc.) for the given paths. If the path is already
  performing a configured continuous action, the path will be skipped.

* `csm off GROUP|PATH …`: Disable any persistent action for the given paths
  (unmount, no longer perform periodic syncs, etc.). If the path is
  configured for a continuous action that is already disabled, the path
  will be skipped.

* `csm show GROUP|PATH …`: Display the name and description of the remote
  for the paths, followed by a listing of the files and directories at the
  top level of that remote.

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
user's home directory will be substituted. (`~NAME` substitutions for home
directories will not work.)

The config file contains a section for each path, followed by key-value
pairs for the configuration. E.g.,

    ['~/cloud/foo']
    description = 'The foo files.'  # (optional)
    groups = [ 'all', 'mounts', ]   # (optional)
    remote = 'my-foo:/bar/baz'      # rclone remote `my-foo:` w/subpath
    action = 'bisync'               # see actions below
    period = '5m'                   # (optional) see "Periodic Actions" below

### Remotes

Remotes are given in standard [rclone] format: remote name followed by an
optional path. (This allows copying/syncing/etc. to a subdir of an rclone
remote.)

### Actions

The `action` key may have one of the following values:

* `mount`: Mount the remote on _path,_ or unmount if the `off` command is
  given. (See [`rclone mount`].)

* `bisync`: Bidirectional sync of remote with _path,_ downloading and
  uploading new and changed files and removing files that have been removed
  on the other side. (See `rclone bidir` for more information.)

* `sync-rm`: Copy all files from the remote to _path,_ overwriting any
  locally changed files and removing any files not on the remote.
  (See `rclone sync`.)

* `sync-save`: As sync-rm above, but keep a backup (see "Backups" below) of
  any files that are changed or would be removed. (See `rclone sync`.)

* `push-rm`, `push-save`: As with `sync-*` except from _path_ to the remote.

#### Backups

`copy-*` and `push-*` commands may save copies of files that it changes or
removes in the local copy. These are stored in a `.old/` directory under
the root of the path, with a subdirectory named for the timestamp of the
copy/push. E.g., if `foo/bar` is present on the client but deleted on the
server, a `copy-save-rm` or `copy-save-all` will first copy `foo/bar` to
`.old/2025-12-28t13:55:47/foo/bar` before deleting `foo/bar`. This applies
only to files; directories will not be preserved.

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
[`rclone mount`]: https://rclone.org/commands/rclone_mount/
[interactive]: https://rclone.org/docs/#interactive
[rclone]: https://rclone.org/
