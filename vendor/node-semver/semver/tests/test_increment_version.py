# -*- coding:utf-8 -*-
import pytest
# node-semver/test/index.js
# import logging
# logging.basicConfig(level=logging.DEBUG, format="%(message)s")

cands =   [
    ['1.2.3', 'major', '2.0.0', False],
    ['1.2.3', 'minor', '1.3.0', False],
    ['1.2.3', 'patch', '1.2.4', False],
    ['1.2.3tag', 'major', '2.0.0', True],
    ['1.2.3-tag', 'major', '2.0.0', False],
    ['1.2.3', 'fake', None, False],
    ['1.2.0-0', 'patch', '1.2.0', False],
    ['fake', 'major', None, False],
    ['1.2.3-4', 'major', '2.0.0', False],
    ['1.2.3-4', 'minor', '1.3.0', False],
    ['1.2.3-4', 'patch', '1.2.3', False],
    ['1.2.3-alpha.0.beta', 'major', '2.0.0', False],
    ['1.2.3-alpha.0.beta', 'minor', '1.3.0', False],
    ['1.2.3-alpha.0.beta', 'patch', '1.2.3', False],
    ['1.2.4', 'prerelease', '1.2.5-0', False],
    ['1.2.3-0', 'prerelease', '1.2.3-1', False],
    ['1.2.3-alpha.0', 'prerelease', '1.2.3-alpha.1', False],
    ['1.2.3-alpha.1', 'prerelease', '1.2.3-alpha.2', False],
    ['1.2.3-alpha.2', 'prerelease', '1.2.3-alpha.3', False],
    ['1.2.3-alpha.0.beta', 'prerelease', '1.2.3-alpha.1.beta', False],
    ['1.2.3-alpha.1.beta', 'prerelease', '1.2.3-alpha.2.beta', False],
    ['1.2.3-alpha.2.beta', 'prerelease', '1.2.3-alpha.3.beta', False],
    ['1.2.3-alpha.10.0.beta', 'prerelease', '1.2.3-alpha.10.1.beta', False],
    ['1.2.3-alpha.10.1.beta', 'prerelease', '1.2.3-alpha.10.2.beta', False],
    ['1.2.3-alpha.10.2.beta', 'prerelease', '1.2.3-alpha.10.3.beta', False],
    ['1.2.3-alpha.10.beta.0', 'prerelease', '1.2.3-alpha.10.beta.1', False],
    ['1.2.3-alpha.10.beta.1', 'prerelease', '1.2.3-alpha.10.beta.2', False],
    ['1.2.3-alpha.10.beta.2', 'prerelease', '1.2.3-alpha.10.beta.3', False],
    ['1.2.3-alpha.9.beta', 'prerelease', '1.2.3-alpha.10.beta', False],
    ['1.2.3-alpha.10.beta', 'prerelease', '1.2.3-alpha.11.beta', False],
    ['1.2.3-alpha.11.beta', 'prerelease', '1.2.3-alpha.12.beta', False],
    ['1.2.0', 'preminor', '1.3.0-0', False],
    ['1.2.0', 'premajor', '2.0.0-0', False],
    ['1.2.0', 'preminor', '1.3.0-0', False],
    ['1.2.0', 'premajor', '2.0.0-0', False]
]

# cands =   [
#     ['1.2.3-alpha.0', 'prerelease', '1.2.3-alpha.1', False],
# ]


@pytest.mark.parametrize("pre, what, wanted, loose", cands)
def test_it(pre, what, wanted, loose):
    from semver import inc
    assert inc(pre, what, loose) == wanted
