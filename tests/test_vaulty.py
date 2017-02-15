from unittest.mock import MagicMock

import pytest

from vaulty import REPLState


@pytest.fixture
def state():
    def list(path):
        if path == 'foo/bar/':
            return {'data': {'keys': ['a', 'b', 'c']}}

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
