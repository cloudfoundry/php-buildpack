# -*- coding:utf-8 -*-
import pytest
# node-semver/test/index.js
# import logging
# logging.basicConfig(level=logging.DEBUG, format="%(message)s")

cands = [
    ['=1.2.3', '1.2.3'],
    ['01.02.03', '1.2.3'],
    ['1.2.3-beta.01', '1.2.3-beta.1'],
    ['   =1.2.3', '1.2.3'],
    ['1.2.3foo', '1.2.3-foo']
]


@pytest.mark.parametrize("loose, strict", cands)
def test_it(loose, strict):
    import pytest
    from semver import make_semver, eq

    with pytest.raises(ValueError):
        make_semver(loose, False)

    lv = make_semver(loose, True)
    assert lv.version == strict
    assert eq(loose, strict, True) is True

    with pytest.raises(ValueError):
        eq(loose, strict, False)

    with pytest.raises(ValueError):
        make_semver(strict, False).compare(loose)


cands = [
    ['>=01.02.03', '>=1.2.3'],
    ['~1.02.03beta', '>=1.2.3-beta <1.3.0-0']
]


@pytest.mark.parametrize("loose, comps", cands)
def test_it_for_range(loose, comps):
    import pytest
    from semver import make_range

    with pytest.raises(ValueError):
        make_range(loose, False)

    assert make_range(loose, True).range == comps
