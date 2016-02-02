# Cross Functional Process Explorer

# Vision
One utility, supporting at least OS X and Linux, replacing
* `ps`, but with sensible defaults
* `pgrep` (running `px root` should list only root's processes, running
`px java` should list only java processes)
* `top` (by running `watch px`)
* `pstree` (running `px 1234` should show PID 1234 in a tree, plus a lot of
other information about that process)
* Possibly `lsof`
* Possibly `iotop`

# Installation

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
* Python 2.7 + `virtualenv` if that's available on a vanilla Ubuntu Precise
system
* Python 2.7 + compile to a binary executable that's runnable on a vanilla
Ubuntu Precise system

# Implementation Language (Python 2.7)
Language requirements:
1. There must be a useable process listing library for OS X and Linux
2. It must be available on a vanilla Ubuntu 12.4 Precise system
3. It must be available on a vanilla OS X 10.11 system
4. It must be possible to install the resulting product together with all its
dependencies in a single directory *or* possible to compile everything into one
static binary

Python-2.7 is available on Ubuntu 12.4 Precise and OS X, it has
[psutil](https://pythonhosted.org/psutil/), `virtualenv` and a number of options
for turning programs into statically linked binaries.

# TODO for initial release
Make `px` list all processes with:
* PID
* owner
* memory usage (in % of available RAM or in bytes?)
* used CPU time
* full command line

Output should be in table format just like `top` or `ps`.

Output should be sorted by `score`, with `score` being `(used CPU time) *
(memory usage)`. The intention here is to put the most interesting processes on
top.

We also need to add a section about installation instructions to this document.

# TODO: Move to public GitHub
Now that we have something that can actually be useful to somebody, move to
public GitHub.

Make sure there's a Development section in this README helping people get set
up.

# TODO for easy installation
* Decide on `virtualenv` + `curl` script vs static binaries
* Either make a `curl` script, test on OS X and vanilla Ubuntu 12.4 Precise and
commit that to the repo, or...
* ... create a compile-static-binaries build script together with documentation
on how to make releases using that script
* Update the Installation Instructions in this document with this new
information.

# TODO Continuous Integration
Add a `.travis.yml` config to the project that:
* Runs `flake8` on the code
* Tests the code on OS X
* Tests the code on Linux
* Can or should Travis create binaries for us? Think about security vs
ease-of-deployment.

# TODO `pgrep` replacement
* If we get one command line argument, only show processes matching that string
as either a user or the name of an executable.

# TODO `top` replacement
* Print system load before the process listing
* Maybe add a `--top` / `--top=5s` flag which samples the system for one second
(or five) and adds a CPU usage column to the output
* Maybe add a command line option for truncating output at screen width

# TODO `pstree` (and partly `lsof`) replacement
* If we get something looking like a PID as a command line argument, for that
PID show:
 * The process in a tree with all parents up to the top and all children down
 * A list of all open files, pipes and sockets
 * For each pipe, print the process at the other end of that pipe
 * For each socket, print where it's going

# TODO `iotop` replacement
* When given the `--top` flag and enough permissions, record per process IO
usage and present that in one or more columns.
