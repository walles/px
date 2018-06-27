package(default_visibility = ["//visibility:public"])

load("@my_deps//:requirements.bzl", "requirement")

py_binary(
    name = "px",
    srcs = glob(["px/**/*.py"]),
    deps = [
        # The name in quotes here must match an entry in requirements.txt
        requirement("docopt"),
        requirement("python-dateutil")
        ],
)

py_test(
    name = "unittests",

    srcs = glob(["tests/**/*.py"]) + glob(["px/**/*.py"]),
    main = "tests/run-tests.py",

    deps = [
        # The name in quotes here must match an entry in requirements.txt
        requirement("docopt"),
        requirement("python-dateutil")
        ],
)
