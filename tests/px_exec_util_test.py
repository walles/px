import subprocess

from px import px_exec_util


def test_exec_false_no_check():
    assert px_exec_util.run(["false"]) == ""


def test_exec_true_with_check():
    assert px_exec_util.run(["true"], check_exitcode=True) == ""


def test_exec_false_with_check():
    try:
        px_exec_util.run(["false"], check_exitcode=True)
        assert False and "We should never get here"
    except subprocess.CalledProcessError:
        # This is the exception we want, done!
        pass
