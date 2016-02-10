# Design Decisions

# Implementation Language (Go)
Language requirements:

1. There must be a useable process listing library for OS X and Linux
2. It must be available on a vanilla Ubuntu 12.4 Precise system
3. It must be available on a vanilla OS X 10.11 system
4. It must be possible to install the resulting product together with all its
dependencies in a single directory / executable file
5. It must be possible to `setuid` the binary to `root` on OS X; this is
required for reading CPU and memory usage on OS X, and is how the native `ps` is
installed.

## Go
* can make both Linux and OS X binaries
* has a [`psutil` port](https://github.com/shirou/gopsutil)
* builds single-file static binaries by default that can be `setuid` `root`

## Python-2.7
* is available on Ubuntu 12.4 Precise and OS X
* has [psutil](https://pythonhosted.org/psutil/) for listing processes
* has [`Pants`/`pex`](https://pantsbuild.github.io/python-readme.html) for
building single-file binaries
* had no [obvious](http://www.faqs.org/faqs/unix-faq/faq/part4/section-7.html)
way of making binaries that could be `setuid` `root` that we could find.

## Installation
It must be simple to install in a random directory on a vanilla
Ubuntu 12.4 Precise system. In this case that's because what Github Enterprise
2.3.3 is running on.

"Simple to install" in this case means:
* no root access required
* download single-file binary and run it or copy to `/usr/local/bin`
* it should be possible to make symlinks to this binary and execute it through
those
