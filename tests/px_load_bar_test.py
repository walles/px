from px import px_load_bar


def get_load_bar(physical=None, logical=None):
    return_me = px_load_bar.PxLoadBar(physical=physical, logical=logical)
    return_me.normal = u'n'
    return_me.inverse = u'i'
    return_me.red = u'r'
    return_me.yellow = u'y'
    return_me.green = u'g'
    return return_me


def test_single_core_no_ht():
    test_me = get_load_bar(1, 1)

    assert test_me.get_bar(load=0, columns=10) == u'i          n'
    assert test_me.get_bar(load=1, columns=10) == u'g          n'
    assert test_me.get_bar(load=2, columns=10) == u'g     r     n'
    assert test_me.get_bar(load=4, columns=12) == u'g   r         n'

    assert test_me.get_bar(load=0.5, columns=12) == u'g      i      n'


def test_single_core_with_ht():
    test_me = get_load_bar(1, 2)

    assert test_me.get_bar(load=0, columns=10) == u'i          n'
    assert test_me.get_bar(load=1, columns=10) == u'g          n'
    assert test_me.get_bar(load=2, columns=10) == u'g     y     n'
    assert test_me.get_bar(load=3, columns=12) == u'g    y    r    n'
    assert test_me.get_bar(load=4, columns=12) == u'g   y   r      n'


def test_dual_core_no_ht():
    test_me = get_load_bar(2, 2)

    assert test_me.get_bar(load=0, columns=10) == u'i          n'
    assert test_me.get_bar(load=2, columns=10) == u'g          n'
    assert test_me.get_bar(load=4, columns=10) == u'g     r     n'
    assert test_me.get_bar(load=6, columns=12) == u'g    r        n'


def test_rounding():
    test_me = get_load_bar(2, 2)

    assert test_me.get_bar(load=0.49, columns=2) == u'i  n'
    assert test_me.get_bar(load=0.51, columns=2) == u'g i n'
    assert test_me.get_bar(load=1000, columns=2) == u'r  n'
