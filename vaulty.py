import logging
import readline
import os
import sys

import hvac


LOG_FILENAME = '/tmp/completer.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


class REPLState:
    pwd = 'secret/'
    home = 'secret/'
    _last_tab_path = None
    _options = []

    def __init__(self, vault_client):
        self.vault = vault_client

    def list(self, path):
        try:
            results = state.vault.list(path)['data']['keys']
            self._options = results
            self._last_tab_path = path
            return results
        except TypeError:
            return []

    def readline_completer(self, text, state):
        logging.debug('readline text:%s state:%d', text, state)
        if state > 5:
            # Why does this happen?
            logging.error('infinite loop detected, terminating')
            return None

        if state == 0:
            if self.pwd != self._last_tab_path:
                self.list(self.pwd)
        current_options = [x for x in self._options if x.startswith(text)]
        in_cd = readline.get_line_buffer().startswith('cd ')
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


def repl():
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
        else:
            state.pwd = os.path.normpath(os.path.join(state.pwd, bits[1])) + '/'
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


if __name__ == "__main__":
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
                repl()
            except hvac.exceptions.Forbidden as e:
                print(e)
    except (KeyboardInterrupt, EOFError):
        sys.exit(1)
