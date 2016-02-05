# Design Decisions

# Implementation Language (Python 2.7)
Language requirements:

1. There must be a useable process listing library for OS X and Linux
2. It must be available on a vanilla Ubuntu 12.4 Precise system
3. It must be available on a vanilla OS X 10.11 system
4. It must be possible to install the resulting product together with all its
dependencies in a single directory / executable file

Python-2.7 is available on Ubuntu 12.4 Precise and OS X, it has
[psutil](https://pythonhosted.org/psutil/), `virtualenv` and a number of options
for turning programs into single-file binaries.

## Installation
It must be simple to install in a random directory on a vanilla
Ubuntu 12.4 Precise system. In this case that's because what Github Enterprise
2.3.3 is running on.

"Simple to install" in this case means:
* no root access required
* single command line install (most likely `curl` based)
* everything should end up in one single directory of the user's choosing
* the install process should end with printing the path to the binary
* it should be possible to make symlinks to this binary and execute it through
those

Candidates are:
* Python 2.7 + build with
[Pants](https://pantsbuild.github.io/python-readme.html)
