# -*- coding:utf-8 -*-
import pytest
# node-semver/test/index.js

cands = [
    ['1.2.3', 'v1.2.3', True],
    ['1.2.3', '=1.2.3', True],
    ['1.2.3', 'v 1.2.3', True],
    ['1.2.3', '= 1.2.3', True],
    ['1.2.3', ' v1.2.3', True],
    ['1.2.3', ' =1.2.3', True],
    ['1.2.3', ' v 1.2.3', True],
    ['1.2.3', ' = 1.2.3', True],
    ['1.2.3-0', 'v1.2.3-0', True],
    ['1.2.3-0', '=1.2.3-0', True],
    ['1.2.3-0', 'v 1.2.3-0', True],
    ['1.2.3-0', '= 1.2.3-0', True],
    ['1.2.3-0', ' v1.2.3-0', True],
    ['1.2.3-0', ' =1.2.3-0', True],
    ['1.2.3-0', ' v 1.2.3-0', True],
    ['1.2.3-0', ' = 1.2.3-0', True],
    ['1.2.3-1', 'v1.2.3-1', True],
    ['1.2.3-1', '=1.2.3-1', True],
    ['1.2.3-1', 'v 1.2.3-1', True],
    ['1.2.3-1', '= 1.2.3-1', True],
    ['1.2.3-1', ' v1.2.3-1', True],
    ['1.2.3-1', ' =1.2.3-1', True],
    ['1.2.3-1', ' v 1.2.3-1', True],
    ['1.2.3-1', ' = 1.2.3-1', True],
    ['1.2.3-beta', 'v1.2.3-beta', True],
    ['1.2.3-beta', '=1.2.3-beta', True],
    ['1.2.3-beta', 'v 1.2.3-beta', True],
    ['1.2.3-beta', '= 1.2.3-beta', True],
    ['1.2.3-beta', ' v1.2.3-beta', True],
    ['1.2.3-beta', ' =1.2.3-beta', True],
    ['1.2.3-beta', ' v 1.2.3-beta', True],
    ['1.2.3-beta', ' = 1.2.3-beta', True],
    ['1.2.3-beta+build', ' = 1.2.3-beta+otherbuild', True],
    ['1.2.3+build', ' = 1.2.3+otherbuild', True],
    ['1.2.3-beta+build', '1.2.3-beta+otherbuild', False],
    ['1.2.3+build', '1.2.3+otherbuild', False],
    ['  v1.2.3+build', '1.2.3+otherbuild', False]
]


@pytest.mark.parametrize("v0, v1, loose", cands)
def test_eq(v0, v1, loose):
    from semver import eq
    assert eq(v0, v1, loose) is True


@pytest.mark.parametrize("v0, v1, loose", cands)
def test_neq(v0, v1, loose):
    from semver import neq
    assert (not neq(v0, v1, loose)) is True


@pytest.mark.parametrize("v0, v1, loose", cands)
def test_cmp(v0, v1, loose):
    from semver import cmp
    assert cmp(v0, "==", v1, loose) is True


@pytest.mark.parametrize("v0, v1, loose", cands)
def test_cmp2(v0, v1, loose):
    from semver import cmp
    assert (not cmp(v0, "!=", v1, loose)) is True


@pytest.mark.parametrize("v0, v1, loose", cands)
def test_cmp3(v0, v1, loose):
    from semver import cmp
    assert (not cmp(v0, "===", v1, loose)) is True


@pytest.mark.parametrize("v0, v1, loose", cands)
def test_cmp4(v0, v1, loose):
    from semver import cmp
    assert cmp(v0, "!==", v1, loose) is True


@pytest.mark.parametrize("v0, v1, loose", cands)
def test_gt(v0, v1, loose):
    from semver import gt
    assert not (gt(v0, v1, loose)) is True


@pytest.mark.parametrize("v0, v1, loose", cands)
def test_gte(v0, v1, loose):
    from semver import gte
    assert (gte(v0, v1, loose)) is True


@pytest.mark.parametrize("v0, v1, loose", cands)
def test_lt(v0, v1, loose):
    from semver import lt
    assert not (lt(v0, v1, loose)) is True


@pytest.mark.parametrize("v0, v1, loose", cands)
def test_lte(v0, v1, loose):
    from semver import lte
    assert (lte(v0, v1, loose)) is True

"""
   var v0 = v[0];
    var v1 = v[1];
    var loose = v[2];
    t.ok(gt(v0, v1, loose), "gt('" + v0 + "', '" + v1 + "')");
    t.ok(lt(v1, v0, loose), "lt('" + v1 + "', '" + v0 + "')");
    t.ok(!gt(v1, v0, loose), "!gt('" + v1 + "', '" + v0 + "')");
    t.ok(!lt(v0, v1, loose), "!lt('" + v0 + "', '" + v1 + "')");
    t.ok(eq(v0, v0, loose), "eq('" + v0 + "', '" + v0 + "')");
    t.ok(eq(v1, v1, loose), "eq('" + v1 + "', '" + v1 + "')");
    t.ok(neq(v0, v1, loose), "neq('" + v0 + "', '" + v1 + "')");
    t.ok(cmp(v1, '==', v1, loose), "cmp('" + v1 + "' == '" + v1 + "')");
    t.ok(cmp(v0, '>=', v1, loose), "cmp('" + v0 + "' >= '" + v1 + "')");
    t.ok(cmp(v1, '<=', v0, loose), "cmp('" + v1 + "' <= '" + v0 + "')");
    t.ok(cmp(v0, '!=', v1, loose), "cmp('" + v0 + "' != '" + v1 + "')");
 """
