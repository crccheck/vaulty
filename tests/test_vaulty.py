from unittest.mock import MagicMock

import pytest

from vaulty import REPLState, cmd_cd, cmd_ls


@pytest.fixture
def state():
    def list(path):
        if path == 'foo/bar/':
            return {'data': {'keys': ['a', 'b', 'c']}}

        if path == 'secret/garden/':
            return {'data': {'keys': ['gnome']}}

    mock_client = MagicMock(list=list)
    return REPLState(mock_client)


# REPLState
###########

def test_constructor(state):
    assert state
    assert state.pwd == 'secret/'


def test_pwd_sets_pwd_oldpwd(state):
    state.pwd = 'hi'
    assert state.pwd == 'hi'
    state.pwd = 'hello'
    assert state.pwd == 'hello'
    assert state.oldpwd == 'hi'


def test_list_stores_results(state):
    state.list('foo/bar/')
    assert state._list_cache['foo/bar/'] == ['a', 'b', 'c']


def test_list_handles_bad_path(state):
    state.list('bad/path/')
    assert 'bad/path/' not in state._list_cache


# Commands
##########

def test_cd(state):
    """cd"""
    state.pwd = 'foo/narf/'
    out = cmd_cd(state)
    assert out is None
    assert state.pwd == state.home


def test_cd__(state):
    """cd -"""
    state.pwd = 'foo/narf/'
    state.oldpwd = 'bar/barf/'
    out = cmd_cd(state, '-')
    assert out == 'bar/barf/ is not a valid path'
    assert state.pwd == 'foo/narf/'

    state.pwd = 'foo/narf/'
    state.oldpwd = 'foo/bar/'
    out = cmd_cd(state, '-')
    assert out is None
    assert state.pwd == 'foo/bar/'


def test_cd_somedir(state):
    """cd somedir"""
    out = cmd_cd(state, 'somedir')
    assert out == 'secret/somedir/ is not a valid path'
    assert state.pwd == 'secret/'

    out = cmd_cd(state, 'garden')
    assert out is None
    assert state.pwd == 'secret/garden/'


def test_cd_absdir(state):
    """cd /somedir"""
    out = cmd_cd(state, '/somedir')
    assert out == 'somedir/ is not a valid path'
    assert state.pwd == 'secret/'

    out = cmd_cd(state, '/foo/bar')
    assert out is None
    assert state.pwd == 'foo/bar/'


def test_ls_reads_pwd(state):
    state.pwd = 'foo/bar/'
    assert cmd_ls(state) == 'a\nb\nc'


def test_ls_reads_target(state):
    state.pwd = 'foo'
    assert cmd_ls(state, 'bar/') == 'a\nb\nc'


def test_ls_reports_bad_target(state):
    assert 'not a valid path' in cmd_ls(state, 'who/knows/where/this/goes')
