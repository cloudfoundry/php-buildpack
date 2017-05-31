# -*- coding:utf-8 -*-
def test_it():
    from semver import max_satisfying
    assert max_satisfying(["2.4.3", "2.4.4", "2.5b", "3.0.1-b"], "~2", True) == "2.5b"


def test_it2():
    from semver import max_satisfying
    assert max_satisfying(["2b", "3.0.1-b"], "~2", True) == "2b"


def test_it3():
    from semver import max_satisfying
    assert max_satisfying(["2.5b", "v2010.07.06dev"], "~2", True) == "2.5b"
