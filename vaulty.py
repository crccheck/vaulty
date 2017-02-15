import logging
import readline
import os
import sys

import hvac


LOG_FILENAME = '/tmp/completer.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


class REPLState:
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

    @property
    def pwd(self):
        return self._pwd

    @pwd.setter
    def pwd(self, new_pwd):
        self.oldpwd = self._pwd
        self._pwd = new_pwd

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
        in_cd = readline.get_line_buffer().startswith('cd ')  # TODO this is awkward
        if in_cd:
            current_options = [x for x in current_options if x.endswith('/')]
        if len(current_options) == 1:
            return current_options[0]

        if current_options:
            print()
            print('\n'.join(current_options))
            # print(text, end='')
            print(f'{self.pwd}> {readline.get_line_buffer()}', end='')
            sys.stdout.flush()
        return None


def repl(state):
    in_text = input(f'{state.pwd}> ')
    bits = in_text.strip().split()

    if not bits:
        return

    if bits[0] == 'pwd':
        print(state.pwd)
        return

    if bits[0] == 'ls' or bits[0] == 'l':
        # TODO list bits[1] if it exists
        print('\n'.join(state.list(state.pwd)))
        return

    if bits[0] == 'cd':
        if len(bits) == 1:
            state.pwd = state.home
            return

        if bits[1] == '-':
            new_pwd = state.oldpwd or state.pwd
        else:
            new_pwd = os.path.normpath(os.path.join(state.pwd, bits[1])) + '/'
        if state.list(new_pwd):
            state.pwd = new_pwd
            return

        print(f'{new_pwd} is not a valid path')
        return

    if bits[0] == 'cat':
        if len(bits) != 2:
            return 'USAGE: cat <path>'

        secret_path = os.path.normpath(os.path.join(state.pwd, bits[1]))
        try:
            for key, value in state.vault.read(secret_path)['data'].items():
                print(f'{key}={value}')
        except TypeError:
            print(f'{bits[1]} does not exist')
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
