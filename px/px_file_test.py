import px_file


def test_lsof_to_files():
    lsof = ""

    lsof += '\0'.join(["p123", "\n"])
    lsof += '\0'.join(["fcwd", "a ", "tDIR", "n/", "\n"])
    lsof += '\0'.join(["f5", "ar", "tREG", "ncontains\nnewline", "\n"])
    lsof += '\0'.join(["f6", "aw", "tREG", "n/somefile", "\n"])
    lsof += '\0'.join(["p456", "\n"])
    lsof += '\0'.join(["f7", "au", "tREG", "n/someotherfile", "\n"])

    files = px_file.lsof_to_files(lsof)

    assert len(files) == 4

    assert files[0].pid == 123
    assert files[0].access is None
    assert files[0].type == "DIR"
    assert files[0].name == "/"

    assert files[1].pid == 123
    assert files[1].access == "r"
    assert files[1].type == "REG"
    assert files[1].name == "contains\nnewline"

    assert files[2].pid == 123
    assert files[2].access == "w"
    assert files[2].type == "REG"
    assert files[2].name == "/somefile"

    assert files[3].pid == 456
    assert files[3].access == "rw"
    assert files[3].type == "REG"
    assert files[3].name == "/someotherfile"
