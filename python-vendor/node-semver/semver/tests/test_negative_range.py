# -*- coding:utf-8 -*-
import pytest
# node-semver/test/index.js
# import logging
# logging.basicConfig(level=logging.DEBUG, format="%(message)s")

cands =   [
    ['1.0.0 - 2.0.0', '2.2.3', False],
    ['1.0.0', '1.0.1', False],
    ['>=1.0.0', '0.0.0', False],
    ['>=1.0.0', '0.0.1', False],
    ['>=1.0.0', '0.1.0', False],
    ['>1.0.0', '0.0.1', False],
    ['>1.0.0', '0.1.0', False],
    ['<=2.0.0', '3.0.0', False],
    ['<=2.0.0', '2.9999.9999', False],
    ['<=2.0.0', '2.2.9', False],
    ['<2.0.0', '2.9999.9999', False],
    ['<2.0.0', '2.2.9', False],
    ['>=0.1.97', 'v0.1.93', True],
    ['>=0.1.97', '0.1.93', False],
    ['0.1.20 || 1.2.4', '1.2.3', False],
    ['>=0.2.3 || <0.0.1', '0.0.3', False],
    ['>=0.2.3 || <0.0.1', '0.2.2', False],
    ['2.x.x', '1.1.3', False],
    ['2.x.x', '3.1.3', False],
    ['1.2.x', '1.3.3', False],
    ['1.2.x || 2.x', '3.1.3', False],
    ['1.2.x || 2.x', '1.1.3', False],
    ['2.*.*', '1.1.3', False],
    ['2.*.*', '3.1.3', False],
    ['1.2.*', '1.3.3', False],
    ['1.2.* || 2.*', '3.1.3', False],
    ['1.2.* || 2.*', '1.1.3', False],
    ['2', '1.1.2', False],
    ['2.3', '2.4.1', False],
    ['~2.4', '2.5.0', False], #  >=2.4.0 <2.5.0
    ['~2.4', '2.3.9', False],
    ['~>3.2.1', '3.3.2', False], #  >=3.2.1 <3.3.0
    ['~>3.2.1', '3.2.0', False], #  >=3.2.1 <3.3.0
    ['~1', '0.2.3', False], #  >=1.0.0 <2.0.0
    ['~>1', '2.2.3', False],
    ['~1.0', '1.1.0', False], #  >=1.0.0 <1.1.0
    ['<1', '1.0.0', False],
    ['>=1.2', '1.1.1', False],
    ['1', '2.0.0beta', True],
    ['~v0.5.4-beta', '0.5.4-alpha', False],
    ['<1', '1.0.0beta', True],
    ['< 1', '1.0.0beta', True],
    ['=0.7.x', '0.8.2', False],
    ['>=0.7.x', '0.6.2', False],
    ['<=0.7.x', '0.7.2', False],
    ['<1.2.3', '1.2.3-beta', False],
    ['=1.2.3', '1.2.3-beta', False],
    ['>1.2', '1.2.8', False],
    ['^1.2.3', '2.0.0-alpha', False],
    ['^1.2.3', '1.2.2', False],
    ['^1.2', '1.1.9', False],
    ['blerg', '1.2.3', False],    # invalid ranges never satisfied!
    ['git+https://user:password0123@github.com/foo', '123.0.0', True],
    ['^1.2.3', '2.0.0-pre', False]
]

# cands =   [
#     ['<1.2.3', '1.2.3-beta', False], # anything wrong
# ]


@pytest.mark.parametrize("range_, version, loose", cands)
def test_it(range_, version, loose):
    from semver import satisfies
    assert (not satisfies(version, range_, loose)) is True

