# See: https://github.com/bazelbuild/rules_python
load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")
git_repository(
    name = "io_bazel_rules_python",
    remote = "https://github.com/bazelbuild/rules_python.git",

    # HEAD of master at 2019jan30
    commit = "ebd7adcbcafcc8abe3fd8e5b0e42e10ced1bfe27",
)

# This rule translates the specified requirements.txt into
# @my_deps//:requirements.bzl, which itself exposes a pip_install method.
load("@io_bazel_rules_python//python:pip.bzl", "pip_import")

# FIXME: This rule looks in "external/requirements.txt", how to get it to
# look in the workspace root? After fixing this, remove the "external" symlink
# from the top of the repo.
pip_import(name="my_deps", requirements=":requirements.txt")

# Execute the generated requirements file
load("@my_deps//:requirements.bzl", "pip_install")
pip_install()
