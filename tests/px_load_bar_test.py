from px import px_load_bar


def get_load_bar(physical=None, logical=None):
    return_me = px_load_bar.PxLoadBar(1, 1)
    return_me.normal = b'n'
    return_me.inverse = b'i'
    return_me.red = b'r'
    return_me.yellow = b'y'
    return_me.green = b'g'
    return return_me


def test_single_core_no_ht():
    test_me = get_load_bar(1, 1)

    assert test_me.get_bar(load=0, columns=10) == b'i     n     '
    assert test_me.get_bar(load=1, columns=10) == b'g     n     '
    assert test_me.get_bar(load=2, columns=10) == b'g     r     n'
    assert test_me.get_bar(load=4, columns=12) == b'g   r         n'

    assert test_me.get_bar(load=0.5, columns=12) == b'g   i   n      '


def test_single_core_with_ht():
    test_me = get_load_bar(1, 2)

    assert test_me.get_bar(load=0, columns=10) == b'i     n     '
    assert test_me.get_bar(load=1, columns=10) == b'g     n     '
    assert test_me.get_bar(load=2, columns=10) == b'g     y     n'
    assert test_me.get_bar(load=3, columns=12) == b'g    y    r    n'
    assert test_me.get_bar(load=4, columns=12) == b'g   y   r      n'


def test_dual_core_no_ht():
    test_me = get_load_bar(2, 2)

    assert test_me.get_bar(load=0, columns=10) == b'i     n     '
    assert test_me.get_bar(load=2, columns=10) == b'g     n     '
    assert test_me.get_bar(load=4, columns=10) == b'g     r     n'
    assert test_me.get_bar(load=6, columns=12) == b'g   r         n'


def test_rounding():
    test_me = get_load_bar(1, 1)

    assert test_me.get_bar(load=0.49, columns=2) == b'i n '
    assert test_me.get_bar(load=0.51, columns=2) == b'g n '
    assert test_me.get_bar(load=1000, columns=2) == b'r  n'
