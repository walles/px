# FIXME: Load only the test requirements
load("@my_deps//:requirements.bzl", "all_requirements")

# FIXME: Consider this:
# https://groups.google.com/forum/#!topic/bazel-discuss/d1RKUmyve_Q
#
# Should we have one of these rules per test file?

# FIXME: Generate targets for the other tests as well, based on file system contents
py_test(
    name = "px_file_test",

    srcs = [
        'px_file_test.py',
        'testutils.py',
    ],

    deps = [
        "//px",
    ] + all_requirements,
)

# FIXME: Generate an umbrella rule that depends on all generated test rules
