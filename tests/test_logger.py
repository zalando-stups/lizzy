import pytest
from lizzy.logging import DefaultFormatter, DebugFormatter, init_logging


def test_default_format_kv():
    assert DefaultFormatter.format_kv('my_key', '') == '\n     > my_key: ************ EMPTY ************'
    assert DefaultFormatter.format_kv('my_key', 'a\nb') == '\n     > my_key: a\n               b'

    dict_value = {'dict_key': 50 * 'abc '}
    lines = DefaultFormatter.format_kv('my_key', dict_value).strip().splitlines()
    assert len(lines) == 3


def test_debug_format_kv():
    expected_empty = '\n                          my_key │ \x1b[32m************ EMPTY ************\x1b[0m'
    expected_empty_error = '\n                          my_key │ \x1b[31m************ EMPTY ************\x1b[0m'
    assert DebugFormatter.format_kv('my_key', '') == expected_empty
    assert DebugFormatter.format_kv('my_key', '', True) == expected_empty_error

    expected_multiline = '\n                          my_key │ \x1b[32ma\x1b[0m' \
                         '\n                                 │ \x1b[32mb\x1b[0m'
    expected_multiline_error = '\n                          my_key │ \x1b[31ma\x1b[0m' \
                               '\n                                 │ \x1b[31mb\x1b[0m'
    print(repr(DebugFormatter.format_kv('my_key', 'a\nb')))
    assert DebugFormatter.format_kv('my_key', 'a\nb') == expected_multiline
    assert DebugFormatter.format_kv('my_key', 'a\nb', True) == expected_multiline_error

    dict_value = {'dict_key': 50 * 'abc '}
    lines = DebugFormatter.format_kv('my_key', dict_value).splitlines()
    assert len(lines) == 3


def test_init_logger():
    assert init_logging() == DefaultFormatter
    assert init_logging('human') == DebugFormatter
    assert init_logging('default') == DefaultFormatter
    with pytest.raises(ValueError):
        init_logging('something_else')
