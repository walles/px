load("@my_deps//:requirements.bzl", "all_requirements")
py_binary(
    name='px',

    # FIXME: Auto generate the sources list
    # FIXME: Handle auto-generated version.py special?
    srcs = [
        '__init__.py',
        'px.py',
        'px_commandline.py',
        'px_cpuinfo.py',
        'px_file.py',
        'px_install.py',
        'px_ipc_map.py',
        'px_load.py',
        'px_load_bar.py',
        'px_loginhistory.py',
        'px_process.py',
        'px_processinfo.py',
        'px_terminal.py',
        'px_top.py',
        'version.py',
    ],

    deps = [

    ] + all_requirements,
)
