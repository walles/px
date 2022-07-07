from px import px_category_bar
from px import px_terminal


def test_render_bar_happy_path():
    names_and_numbers = [("apa", 1000.0), ("bepa", 300.0), ("cepa", 50.0)] + [
        ("long tail", 1)
    ] * 300
    assert px_category_bar.render_bar(10, names_and_numbers) == (
        px_terminal.red(" apa  ")
        + px_terminal.yellow(" b")
        + px_terminal.blue(" ")
        + px_terminal.inverse_video(" ")
    )


def test_render_bar_happy_path_unicode():
    names_and_numbers = [("åpa", 1000.0), ("bäpa", 300.0), ("cäpa", 50.0)] + [
        ("lång svans", 1)
    ] * 300
    assert px_category_bar.render_bar(10, names_and_numbers) == (
        px_terminal.red(" åpa  ")
        + px_terminal.yellow(" b")
        + px_terminal.blue(" ")
        + px_terminal.inverse_video(" ")
    )
