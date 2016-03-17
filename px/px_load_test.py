# -*- coding: utf-8 -*-

import px_load


def test_averages_to_levels():
    l0, l1, l2, peak = px_load.averages_to_levels(0.0, 0.0, 0.0)
    assert (l0, l1, l2, peak) == (0, 0, 0, 1.0)

    l0, l1, l2, peak = px_load.averages_to_levels(0.124, 0.126, 1.0)
    assert (l0, l1, l2, peak) == (0, 1, 4, 1.0)

    l0, l1, l2, peak = px_load.averages_to_levels(0.874, 0.876, 1.0)
    assert (l0, l1, l2, peak) == (3, 4, 4, 1.0)


def test_levels_to_graph():
    # Arrays of uneven lengths shall be left padded with an empty column. So
    # this test case wants: "padding=0, 0", "1, 2", "3, 4".
    assert px_load.levels_to_graph([0, 1, 2, 3, 4]) == u"⠀⣠⣾"

    assert px_load.levels_to_graph([]) == ""
    assert len(px_load.levels_to_graph([0])) == 1
    assert len(px_load.levels_to_graph([1, 2])) == 1
    assert len(px_load.levels_to_graph([3, 4, 1])) == 2
    assert len(px_load.levels_to_graph([1] * 15)) == 8


def test_get_load_string():
    assert px_load.get_load_string((0.1, 0.2, 0.3)).endswith("scale 0-1.0)")
    assert px_load.get_load_string((0.1, 0.2, 3.0)).endswith("scale 0-3.0)")
    assert px_load.get_load_string((0.1, 0.2, 1.135135)).endswith("scale 0-1.1)")
