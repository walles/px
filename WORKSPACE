workspace(name="px")

git_repository(
    name = "io_bazel_rules_python",
    remote = "https://github.com/bazelbuild/rules_python.git",

    # master branch as of 2018jun20
    commit = "8b5d0683a7d878b28fffe464779c8a53659fc645",
)

# This rule translates the specified requirements.txt into
# @my_deps//:requirements.bzl, which itself exposes a pip_install method.
load("@io_bazel_rules_python//python:pip.bzl", "pip_import")
pip_import(
   name = "my_deps",
   requirements = "//:requirements.txt",
)

# Load the pip_install symbol for my_deps, and create the dependencies'
# repositories.
load("@my_deps//:requirements.bzl", "pip_install")
pip_install()
