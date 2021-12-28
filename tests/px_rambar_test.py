# coding=utf-8

import os
import sys

from px import px_rambar
from px import px_terminal


def test_render_bar_happy_path():
    names_and_numbers = [(u"apa", 1000), (u"bepa", 300), (u"cepa", 50)] + [
        (u"long tail", 1)
    ] * 300
    assert px_rambar.render_bar(10, names_and_numbers) == (
        px_terminal.red(u" apa  ")
        + px_terminal.yellow(u" b")
        + px_terminal.blue(u" ")
        + px_terminal.inverse_video(u" ")
    )


def test_render_bar_happy_path_unicode():
    names_and_numbers = [(u"åpa", 1000), (u"bäpa", 300), (u"cäpa", 50)] + [
        (u"lång svans", 1)
    ] * 300
    assert px_rambar.render_bar(10, names_and_numbers) == (
        px_terminal.red(u" åpa  ")
        + px_terminal.yellow(u" b")
        + px_terminal.blue(u" ")
        + px_terminal.inverse_video(u" ")
    )
