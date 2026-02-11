from    argparse import  ArgumentParser, Namespace
from    collections.abc  import Sequence
from    datetime  import datetime, timezone
from    pathlib  import Path
from    subprocess  import PIPE, Popen, run
import  shutil
import  sys

from    columnize  import columnize
from    csm.config  import Config, ConfigError, SyncPath, rclone_remotes

####################################################################
#   Commands are used in the subparser definitions, and so must
#   be defined before parseargs().

def cmd_on(conf:Config, args:Namespace):
    for sp in conf.expand_groups(args.path):
        action_on(args, sp)

def cmd_off(conf:Config, args:Namespace):
    raise RuntimeError('XXX write me')

def cmd_show(conf:Config, args:Namespace):
    for sp in conf.expand_groups(args.path):
        print(f'• Path: {sp.path}')
        print(f'  Action: {sp.action}  Remote: {sp.remote}')

        width = shutil.get_terminal_size().columns - 2

        #   XXX should use JSON output here and build a nicer (single-line)
        #   display that starts with used and free space.
        result = run(['rclone', 'about', sp.remote],
            capture_output=True, text=True, check=True)
        about = list(filter(lambda s: s, result.stdout.strip().split('\n')))
        about = [' '.join(s.split()) for s in about]    # merge multiple spaces
        if about:
            print('\n'.join('  ' + line
                for line in columnize(about, displaywidth=width).split('\n')
                if line != ''))

        if not args.show_verbose:
            return

        result = run(['rclone', 'lsf', sp.remote],
            capture_output=True, text=True, check=True)
        fnames = ['Root listing:'] + result.stdout.strip().split('\n')
        print('\n'.join('  ' + line
            for line in columnize(fnames, displaywidth=width).split('\n')
            if line != ''))

def cmd_list(conf:Config, args:Namespace):
    sps = conf.values()
    awidth = max(len(c.action) for c in sps)
    pwidth = max(len(c.prettypath) for c in sps)
    for c in sps:
        print(f'{c.action:{awidth}}  {c.prettypath:{pwidth}}  {c.description}')

def cmd_groups(conf:Config, args:Namespace):
    raise RuntimeError('XXX write me')

#   XXX missing commands:
#   `reconnect`? (if necessary)

####################################################################
#   Main, args, config

def main():
    args = parseargs()
    #   XXX should catch ConfigError for both lines below
    try:
        args.func(readconfig(args.config), args)
    except ConfigError as err:
        die(2, f'config error: {str(err)}')

def parseargs(argv:Sequence[str]=sys.argv[1:]):
    p = ArgumentParser(prog='csm',
        description='Manage mount/copy/sync of cloud file storage via rclone')
    p.add_argument('--dry-run', '-n', action='store_true',
        help='show what would be done without performing the action')
    p.add_argument('--interactive', '-i', action='store_true',
        help='interactive mode (as in rclone)')
    p.add_argument('--progress', '-p', action='store_true',
        help='show progress of transfer')
    p.add_argument('--verbose', '-v', action='store_true', help='verbose output')
    p.add_argument('-c', '--config', metavar='CONFFILE',
        default='~/.config/rclone/cloud-sync-manager.toml',
        help='configuration file (default: %(default)s)')

    sp = p.add_subparsers(dest='cmd', required=True, help='subcommand')

    on = sp.add_parser('on', help='perform configured action for path or group')
    on.set_defaults(func=cmd_on)
    on.add_argument('path', nargs='*', help='path or group to activate')

    off = sp.add_parser('off', help='deactivate persistent action for path or group')
    off.set_defaults(func=cmd_off)
    off.add_argument('path', nargs='*', help='path or group to deactivate')

    show = sp.add_parser('show',
        help='display remote name, path, description, and top-level listing')
    show.set_defaults(func=cmd_show)
    show.add_argument('-v', '--verbose', dest='show_verbose', action='store_true',
        help='display additional information about each path and its remote')
    show.add_argument('path', nargs='*', help='path or group to show')

    list = sp.add_parser('list', help='list all known paths')
    list.set_defaults(func=cmd_list)

    groups = sp.add_parser('groups', help='list all known groups and their paths')
    groups.set_defaults(func=cmd_groups)

    return p.parse_args(argv)

def readconfig(path):
    cf = Config()
    try:
        with open(Path(path).expanduser(), encoding='utf-8') as f:
            cf.parse_toml(f.read(), rclone_remotes())
    except OSError as err:
        die(1, f'cannot read config file {path}: {err.strerror}')
    return cf

####################################################################
#   Actions

def action_on(args:Namespace, path:SyncPath):
    #   If we are doing an action on a path, create it.
    path.path.mkdir(exist_ok=True, parents=True)
    match path.action:
        case 'mount':
            rclone(path, args, 'mount',
                '-vv',                          # essentially a debugging mode
               #'--daemon',

                #   Our only protection against mounting over an existing
                #   mount is that --allow-non-empty is not the ddefault.
                #   But that should be good enough.

                #   We do fairly heavy caching to make this slow remote
                #   filesystem feel a bit more like a bisync/Dropbox style.
                #   --cache-dir ~/.cache/rclone  by default, but be careful
                #   not to remove bisync caches also under that dir.
                '--vfs-cache-mode=full',        # OFF|minimal|writes|full
                #   Because we mount some pretty large remotes (100+ GiB).
                '--vfs-cache-max-size=3GiB',    # default OFF
                '--vfs-cache-max-age=1h',       # default 1h
                #   On-disk read-ahead, beyond the in memory amount that
                #   --buffer-size will fetch. (Not clear how --max-read-ahead
                #   relates to these.)
                '--vfs-read-ahead', '512K',     # on-disk read

                #   It's assumed that most machines on which this is used
                #   are self-owned, so typically you want root reading your
                #   private files. But this is no longer available; see
                #   • https://github.com/bazil/fuse/issues/144
                #'--allow-root',
                )

        case 'bisync':
            #   XXX untested!
            raise RuntimeError(f'XXX write action: {path.action}')
            rclone(path, args, 'bisync',
                '--delete-after',                   # default
                '--track-renames', '--links')

        case 'sync-rm':
            rclone(path, args, 'sync',
                '--delete-after',                   # default
                '--track-renames', '--links')

        case 'sync-save':
            rclone(path, args, 'sync',
                '--delete-after',                   # default
                '--track-renames', '--links',
                '--backup-dir', backup_dir(path))

        case 'push-rm':
            raise RuntimeError(f'XXX write action: {path.action}')

        case 'push-save':
            raise RuntimeError(f'XXX write action: {path.action}')

        #   Can't have an unknown action here; would have been caught when
        #   parsing config.

def action_off(args:Namespace, path:SyncPath):
    #   Most of these need do nothing.
    match path.action:
        case 'mount':
            raise RuntimeError(f'XXX write action: {path.action}')
            # Linux:    fusermount -u /path/to/local/mount
            # OS X:     umount /path/to/local/mount
        case 'bisync':      ...
        case 'sync-rm':     ...
        case 'sync-save':   ...
        case 'push-rm':     ...
        case 'push-save':   ...

def rclone(sp:SyncPath, args:Namespace, *cmdparts:str):
    ''' Run `rclone` with the source and destination from the given
        `SyncPath` `sp`, using all the `rclone` command line `args`
        (options, command, etc.) passed in.
    '''
    cmd = ['rclone']
    if args.dry_run:  cmd.append('--dry-run')
    if args.verbose:  cmd.append('--verbose')
    if args.progress: cmd.append('--progress')
    cmd.extend([*cmdparts, sp.remote, str(sp.path)])
    if args.verbose:  print(f"• {' '.join(cmd)}")
    run(cmd)

def backup_dir(sp:SyncPath) -> str:
    ''' Return a timestamped backup path suitable for use with rclone's
        ``--backup-path`` option. This must not be in the rclone target
        directory, so we name it after the target directory with a `~`
        appended, with a subdir for each timestamp.
    '''
    dir = sp.path.with_name(sp.path.name + '~')
    return str(dir.joinpath(backup_ts()))

def backup_ts(dt:datetime|None=None) -> str:
    ' Return timestamp for backup dir name in format `{YYYYMMDD-HHMMSS.FFF}`. '
    if dt is None:  dt = datetime.now(timezone.utc)
    ts = dt.strftime('%Y%m%d-%H%M%S')
    ms = f'{dt.microsecond // 1000 :03d}'
    return f'{ts}.{ms}'

####################################################################
#   Misc

def die(exitcode:int, *s):
    warn(*s)
    sys.exit(exitcode)

def warn(*s):
    print('csm:', *s, file=sys.stderr)
