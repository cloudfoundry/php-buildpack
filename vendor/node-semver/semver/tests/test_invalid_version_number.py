# -*- coding:utf-8 -*-
import pytest
# node-semver/test/index.js
# import logging
# logging.basicConfig(level=logging.DEBUG, format="%(message)s")

cands = [
    '1.2.3.4',
    'NOT VALID',
    1.2,
    None,
    'Infinity.NaN.Infinity'
]


@pytest.mark.parametrize("v", cands)
def test_it(v):
    import pytest
    from semver import make_semver
    with pytest.raises(ValueError):
        loose = False
        make_semver(v, loose)





