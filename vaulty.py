import logging
import os
import readline
import shlex
import sys

import hvac


LOG_FILENAME = '/tmp/vaulty-completer.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


class REPLState:
    """
    Stores state for the user's session and also wraps `hvac`.
    """
    _pwd = 'secret/'  # pwd is wrapped to magically make `oldpwd` work
    oldpwd = None
    home = 'secret/'
    # This is only used to help assist tab completion
    _list_cache = {}

    def __init__(self, vault_client):
        self.vault = vault_client

    def list(self, path):
        try:
            results = self.vault.list(path)['data']['keys']
            self._list_cache[path] = results
            return results
        except TypeError:
            # TODO don't fail silently
            return []

    def read(self, path):
        try:
            return self.vault.read(path)['data']
        except TypeError as e:
            # TODO don't fail silently
            logging.warn(e)
            return {}

    @property
    def pwd(self):
        return self._pwd

    @pwd.setter
    def pwd(self, new_pwd):
        self.oldpwd = self._pwd
        self._pwd = new_pwd

    def path_for(self, path=None):
        if path is None:
            path = '.'
        ending = '/' if path[-1] == '/' else ''
        # normpath strips trailing slashes, so restore it if the original had a slash
        return os.path.normpath(os.path.join(self.pwd, path)) + ending

    def readline_completer(self, text, state):
        logging.debug('readline text:%s state:%d', text, state)
        if state > 5:
            # Why does this happen?
            logging.error('infinite loop detected, terminating')
            return None

        if state == 0:
            if self.pwd not in self._list_cache:
                self.list(self.pwd)
        current_options = [x for x in self._list_cache[self.pwd] if x.startswith(text)]
        if len(current_options) == 1:
            return current_options[0]

        if current_options:
            print()
            print('\n'.join(current_options))
            # print(text, end='')
            print(f'{self.pwd}> {readline.get_line_buffer()}', end='')
            sys.stdout.flush()
        return None


def cmd_ls(state, path=None):
    """List secrets and paths in a path, defaults to PWD."""
    if path is None:
        target_path = state.pwd
    else:
        target_path = state.path_for(path)
    results = state.list(target_path)
    if results:
        return('\n'.join(results))

    return f'{path} is not a valid path'


def cmd_rm(state, *paths):
    return 'rm is not implemented yet'


def repl(state):
    in_text = input(f'{state.pwd}> ')
    bits = shlex.split(in_text)

    if not bits:
        return

    if bits[0] == 'pwd':
        print(state.pwd)
        return

    if bits[0] == 'ls' or bits[0] == 'l':
        print(cmd_ls(state, *bits[1:]))
        return

    if bits[0] == 'cd':
        if len(bits) == 1:
            state.pwd = state.home
            return

        if bits[1] == '-':
            new_pwd = state.oldpwd or state.pwd
        else:
            new_pwd = state.path_for(bits[1])
        logging.info('cd %s %s %s', new_pwd, state.list(new_pwd), state.read(new_pwd))
        if state.list(new_pwd) or state.read(new_pwd):
            state.pwd = new_pwd
            return

        print(f'{new_pwd} is not a valid path')
        return

    if bits[0] == 'cat':
        if len(bits) != 2:
            return 'USAGE: cat <path>'

        secret_path = os.path.normpath(os.path.join(state.pwd, bits[1]))
        try:
            for key, value in state.read(secret_path).items():
                print(f'{key}={value}')
        except TypeError:
            print(f'{bits[1]} does not exist')
        return

    if bits[0] == 'rm':
        print(cmd_rm(state, *bits[1:]))
        return

    print('DEBUG:', in_text)


def main():
    path = os.path.expanduser('~/.vault-token')
    if os.path.isfile(path):
        with open(path) as fh:
            token = fh.read().strip()
    client = hvac.Client(url=os.getenv('VAULT_ADDR'), token=token)
    assert client.is_authenticated()
    state = REPLState(client)
    team = os.getenv('VAULT_TEAM', '')
    state.home = state.pwd = os.path.join(state.pwd, team) + '/'
    readline.set_completer(state.readline_completer)
    readline.parse_and_bind('tab: complete')
    # readline.get_completer_delims()
    # readline.set_completer_delims('\n`~!@#$%^&*()-=+[{]}\|;:'",<>/? ')
    readline.set_completer_delims('\n`~!@#$%^&*()=+[{]}\|;:\'",<>/? ')
    try:
        while True:
            try:
                repl(state)
            except hvac.exceptions.Forbidden as e:
                print(e)
    except (KeyboardInterrupt, EOFError):
        sys.exit(1)


if __name__ == "__main__":
    main()
