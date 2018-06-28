package(default_visibility = ["//visibility:public"])

load("@my_deps//:requirements.bzl", "requirement")

py_binary(
    name = "px",
    srcs = glob(["px/**/*.py"]),
    deps = [
        # Names in quotes here must match entries in requirements.txt
        requirement("docopt"),
        requirement("python-dateutil")
        ],
)

py_test(
    name = "unittests",

    srcs = glob(["tests/**/*.py"]) + glob(["px/**/*.py"]),
    main = "tests/run-tests.py",

    deps = [
        # Names in quotes here must match entries in requirements.txt
        requirement("docopt"),
        requirement("python-dateutil"),

        requirement("pytest")
        ],
)
