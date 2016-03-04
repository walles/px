import px_file


def test_lsof_to_files():
    lsof = ""

    lsof += '\0'.join(["p123", "\n"])
    lsof += '\0'.join(["fcwd", "a ", "tDIR", "n/", "\n"])
    lsof += '\0'.join(["f5", "ar", "tREG", "ncontains\nnewline", "\n"])
    lsof += '\0'.join(["f6", "aw", "tREG", "dhej", "n/somefile", "\n"])
    lsof += '\0'.join(["p456", "\n"])
    lsof += '\0'.join(["f7", "au", "tREG", "n/someotherfile", "\n"])
    lsof += '\0'.join(["f7", "a ", "n(revoked)", "\n"])

    files = px_file.lsof_to_files(lsof)

    assert len(files) == 5

    assert files[0].pid == 123
    assert files[0].access is None
    assert files[0].device is None
    assert files[0].type == "DIR"
    assert files[0].name == "[DIR] /"
    assert files[0].plain_name == "/"

    assert files[1].pid == 123
    assert files[1].access == "r"
    assert files[1].device is None
    assert files[1].type == "REG"
    assert files[1].name == "contains\nnewline"
    assert files[1].plain_name == "contains\nnewline"

    assert files[2].pid == 123
    assert files[2].access == "w"
    assert files[2].device == "hej"
    assert files[2].type == "REG"
    assert files[2].name == "/somefile"
    assert files[2].plain_name == "/somefile"

    assert files[3].pid == 456
    assert files[3].access == "rw"
    assert files[3].device is None
    assert files[3].type == "REG"
    assert files[3].name == "/someotherfile"
    assert files[3].plain_name == "/someotherfile"

    assert files[4].pid == 456
    assert files[4].access is None
    assert files[4].device is None
    assert files[4].type == "??"
    assert files[4].name == "[??] (revoked)"
    assert files[4].plain_name == "(revoked)"


def test_get_all():
    files = px_file.get_all()

    # As non-root I get 6000 on my system, 100 should be fine anywhere. And if
    # not, we'll just have to document our finding and lower this value
    assert len(files) > 100
