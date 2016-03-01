import px_process


def test_create_process():
    process_builder = px_process.PxProcessBuilder()
    process_builder.pid = 7
    process_builder.username = "usernamex"
    process_builder.cpu_time = 1.3
    process_builder.memory_percent = 42.7
    process_builder.cmdline = "hej kontinent"
    test_me = px_process.PxProcess(process_builder)

    assert test_me.pid == 7
    assert test_me.user == "usernamex"
    assert test_me.cpu_time_s == "1.300s"
    assert test_me.memory_percent_s == "43%"
    assert test_me.cmdline == "hej kontinent"
