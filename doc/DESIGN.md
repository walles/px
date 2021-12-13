# Design Decisions

# Implementation Language (Python 2.7)

Language requirements:

1. There must be a usable way to list processes for OS X and Linux
2. It must be available on a vanilla Ubuntu 12.4 Precise system
3. It must be available on a vanilla OS X 10.11 system
4. It must be possible to install the resulting product together with all its
   dependencies in a single directory / executable file
5. It must be possible to get as much information as `ps` without being root, on
   both OS X and Linux.

Regarding the last requirement of being able to match `ps` without being root,
the only way to do that on OS X is to actually call `ps` and parse its output.
A lot of information about processes can only be accessed as root, and `ps` just
happens to be installed setuid root to be able to get at this info.

Since `ps`' syntax and output are almost the same between Linux and OS X we can
just call `ps` on Linux as well.

Any language can run `ps` and parse its output really, so 1 and 5 in the above
list doesn't really limit our choice of languages.

What does limit it though is availability on various systems and packaging. One
environment that does fulfill everything in the above list is Python 2.7, which
is available on all of our target platforms.

And using [Pex](https://github.com/pantsbuild/pex) we can turn Python programs
into [platform independent
executables](https://pex.readthedocs.org/en/stable/whatispex.html#whatispex),
which is excellent for distribution. Later replaced by our homegrown
implementation of the same thing, see `make-executable-zip.sh`, that was a lot
faster. I don't know what the requirements for `pex` proper are that makes it
produce big binaries with long startup times.

## Installation

It must be simple to install in a random directory on a vanilla
Ubuntu 12.4 Precise system. In this case that's because what Github Enterprise
2.3.3 is running on.

"Simple to install" in this case means:

- no root access required
- single command line install (most likely `curl` based)
- everything should end up in one single directory of the user's choosing
- the install process should end with printing the path to the binary
- it should be possible to make symlinks to this binary and execute it through
  those

Candidates are:

- Python 2.7 + build with [Pex](https://github.com/pantsbuild/pex) and parse
  `ps` output manually.
