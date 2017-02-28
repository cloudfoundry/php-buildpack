# -*- coding:utf-8 -*-
import pytest
# node-semver/test/index.js
# import logging
# logging.basicConfig(level=logging.DEBUG, format="%(message)s")

cands = [
    [['1.2.3', '1.2.4'], '1.2', '1.2.4', False],
    [['1.2.4', '1.2.3'], '1.2', '1.2.4', False],
    [['1.2.3', '1.2.4', '1.2.5', '1.2.6'], '~1.2.3', '1.2.6', False],
    [['1.1.0', '1.2.0', '1.2.1', '1.3.0', '2.0.0b1', '2.0.0b2', '2.0.0b3', '2.0.0', '2.1.0'], '~2.0.0', '2.0.0', True]
]


@pytest.mark.parametrize("versions, range_, expect, loose", cands)
def test_it(versions, range_, expect, loose):
    from semver import max_satisfying
    assert max_satisfying(versions, range_, loose) == expect
