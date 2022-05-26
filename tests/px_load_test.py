from px import px_load
from px import px_terminal


def test_averages_to_levels():
    l0, l1, l2, peak = px_load.averages_to_levels(0.0, 0.0, 0.0)
    assert (l0, l1, l2, peak) == (0, 0, 0, 1.0)

    # Levels are:
    # 0: 0/6 - 1/6
    # 1: 1/6 - 3/6
    # 2: 3/6 - 5/6
    # 3: 5/6 - 6/6
    l0, l1, l2, peak = px_load.averages_to_levels(
        1.0 / 6.0 - 0.01, 1.0 / 6.0 + 0.01, 1.0
    )
    assert (l0, l1, l2, peak) == (0, 1, 3, 1.0)

    l0, l1, l2, peak = px_load.averages_to_levels(
        5.0 / 6.0 - 0.01, 5.0 / 6.0 + 0.01, 1.0
    )
    assert (l0, l1, l2, peak) == (2, 3, 3, 1.0)


def test_levels_to_graph():
    # Levels 0-3 should be visualized with 1-4 dots. And each character should
    # contain two bars. So this test case wants: "1, 2", "3, 4".
    assert px_load.levels_to_graph([0, 1, 2, 3]) == "⣠⣾"

    # Uneven-numbered level arrays should be padded with an empty column on the
    # left
    assert px_load.levels_to_graph([0, 1, 3]) == "⢀⣼"

    assert px_load.levels_to_graph([]) == ""
    assert len(px_load.levels_to_graph([0])) == 1
    assert len(px_load.levels_to_graph([1, 2])) == 1
    assert len(px_load.levels_to_graph([3, 0, 1])) == 2
    assert len(px_load.levels_to_graph([1] * 15)) == 8


def test_get_load_string():
    px_terminal._enable_color = True
    CSI = "\x1b["
    assert "0.3" + CSI in px_load.get_load_string((0.3, 0.2, 0.1))
    assert "3.0" + CSI in px_load.get_load_string((3.0, 0.2, 0.1))
    assert "1.1" + CSI in px_load.get_load_string((1.135135, 0.2, 0.1))
    assert "2.0" + CSI in px_load.get_load_string((2.0, 3.0, 4.0))
