from    collections.abc  import Sequence
from    pathlib  import Path
from    tomllib  import loads
from    typing  import List, Tuple

class InternalError(RuntimeError): ...

class ConfigError(RuntimeError): ...

class SyncPath(dict):

    def __init__(self, path:Path|str, options:dict):
        self.path = Path(path).expanduser().resolve()
        self.update(options)

    @property
    def prettypath(self) -> str:
        ''' Return this item's path in the nicest possible form for human
            reading, such as by using `~/…` instead of `/home/joe/…`.
            Possibly also use relative paths instead of absolute paths
            where those are shorter. (But not sure about that.)

            XXX This currently just returns the absolute path; we have
            to think about how we want to do this.
        '''
        return str(self.path)

    @property
    def remote(self) -> str:
        try:
            return self['remote']
        except KeyError:
            raise ConfigError(f"Missing 'remote' value for path {self.prettypath}")

    VALID_ACTIONS = (
        'mount',    'bisync',
        'sync-rm',  'sync-save',
        'push-rm',  'push-save',
        )

    @property
    def action(self) -> str:
        a = self.get('action')
        if a not in self.VALID_ACTIONS:
            raise ConfigError(f"invalid action '{a}' for path {self.prettypath}")
        return a

    @property
    def description(self) -> str:
        ' Return description if specified, empty string if not. '
        return self.get('description', '')

class Config():
    ' A dict of `SyncPath`s, indexed by absolute `Path`. '

    def __init__(self, config:str=''):
        self._data:dict = {}
        if config != '':
            self.parse_toml(config)

    ####################################################################
    #   Minimal read-only `dict` interface.
    #   Key handling gives Path isomorphimism.

    def _key(self, key):
        return Path(key).expanduser().resolve()


    def __contains__(self, key):
        return self._data.__contains__(self._key(key))

    def __getitem__(self, key):
        return self._data.__getitem__(self._key(key))

    def get(self, key, default=None):
        return self._data.get(self._key(key), default)

    def __len__(self):  return len(self._data)
    def keys(self):     return self._data.keys()
    def values(self):   return self._data.values()

    ####################################################################

    def parse_toml(self, toml) -> 'Config':
        for heading, values in loads(toml).items():
            sp = SyncPath(heading, values)
            self._data[sp.path] = sp
        return self

    def group(self, groupname:str) -> Tuple[SyncPath, ...]:
        ' Return all config entries in group `groupname`. '
        return tuple([ sp for sp in self.values()
                          if groupname in sp.get('groups', []) ])

    def expand_groups(self, paths_groups:Sequence[str]) -> Tuple[SyncPath, ...]:
        ''' Given a sequence of paths and groups, return a tuple of
            `SyncPath` objects matching the given paths and groups, with
            groups taking precedence over paths if two have the same name.
            If any paths or groups cannot be found in the config, raise
            `KeyError`.
        '''
        res:List[SyncPath] = []
        errs:List[str] = []
        for pg in paths_groups:
            sgs = self.group(pg)
            sg = self.get(pg, None)
            if sgs:                 res.extend(sgs)     # group name priority
            elif sg is not None:    res.append(sg)
            else:                   errs.append(pg)
        if errs:
            raise KeyError(f'Cannot match groups/paths: {errs}')
        return tuple(res)
