[![Build Status](https://travis-ci.org/walles/px.svg?branch=python)](https://travis-ci.org/walles/px)
[![Coverage Status](https://coveralls.io/repos/github/walles/px/badge.svg?branch=python)](https://coveralls.io/github/walles/px?branch=python)

# Cross Functional Process Explorer

# Vision
One utility, supporting at least OS X and Linux, replacing
* :white_check_mark: `ps`, but with sensible defaults (just do `px`)
* :white_check_mark: `pgrep` (running `px root` lists only root's processes,
running `px java` lists only java processes)
* :white_check_mark: `pstree` (running `px 1234` shows PID 1234 in a tree, plus
other information about that process)
* :white_check_mark: `top`, by running `px --top`, or starting `px` through a
symlink ending in `top`. `ptop` anyone?
* Possibly `iotop`

# Demo
![Screenshot](https://raw.githubusercontent.com/walles/px/python/screenshot.png)

This screenshot shows:
* The end of the output from just typing `px`.
  * Note how the newest and the most CPU and memory hungry processes are at the
  end of the list so you can find them without scrolling.
  * Note how the Gradle daemon processes running in Java is listed by class name
  (`GradleDaemon`) rather than the JVM executable name (`java`).
* The result of searching for "terminal" processes.
* The output from the details view of PID 699:
  * The command line has been split with one argument per line. This makes long
  command lines readable.
  * The process tree shows how the Terminal relates to other processes.
  * Details on how long ago Terminal was started, and how much CPU it has been
  using since.
  * A list of other processes started around the same time as Terminal.
  * The IPC section shows that the Terminal is talking to `launchd` and
  `syslogd` using
  [Unix domain sockets](https://en.wikipedia.org/wiki/Unix_domain_socket).

# Installation
* Go to the [Releases](https://github.com/walles/px/releases) page and download
`px.pex` from there. That file is the whole distribution and can be run as it
is on any Python 2.7 equipped system.
* `sudo install px.pex /usr/local/bin/px`
* `sudo ln -s /usr/local/bin/px /usr/local/bin/ptop`

Now, you should be able to run `px`, `px --help` or `ptop` from the command
line. Otherwise please verify that `/usr/local/bin` is in your `$PATH`.

# Usage
Just type `px` or `ptop`, that's a good start!

To exit `ptop`, press "`q`".

Also try `px --help` to see what else `px` can do except for just listing all
processes.

# Development
* Clone: `git clone git@github.com:walles/px.git ; cd px`
* Test: `./ci.sh`
* Build: `./pants binary px`. Your distributable binary is now in `dist/px.pex`.
* Run: `./dist/px.pex`
* To run without first doing the build step: `./pants run px`
* To add dependencies, edit `px/requirements.txt` and `px/BUILD`

# Releasing a new Version
1. Consider updating `screenshot.png` and [the Demo section in this
document](#demo), push those changes.
2. Do `git tag` and think about what the next version number should be.
3. Do ```git tag --annotate 1.2.3``` to set the next version number. The
text you write for this tag will show up as the release description on Github,
write something nice! And remember that the first line is the subject line for
the release.
4. `./pants binary px && ./dist/px.pex --version`, verify that the version
number matches what you just set.
5. `git push --tags`
6. Go to the [Releases](https://github.com/walles/px/releases) page on GitHub,
click your new release, click the `Edit tag` button, then attach your `px.pex`
file that you just built to the release.

# Performance testing
* Store the output of `lsof -F fnaptd0` from a big system in lsof.txt.
* `./px/benchmark_ipcmap.py lsof.txt`

Keeping this benchmark performant is important to be able to use `px` on big
systems.

# TODO `top` replacement
* Disable terminal line wrapping for smoother handling of terminal window
resizes.

# TODO `iotop` replacement
* When given the `--top` flag and enough permissions, record per process IO
usage and present that in one or more columns.

# TODO misc
* Details: When no users were found to be logged in at process start,
automatically detect whether it's because we don't have history that far back or
whether it seems to be that nobody was actually logged in. Inform the user about
the outcome.
* In the px / top views, in the process owner column, maybe print other non-root
process owners of parent processes inside parentheses?
* In the details report, if the current process has a working directory that
isn't `/`, list all other processes that have the same working directory.
* Ignore -E switch on Python command lines


# DONE
* Make `px` list all processes with PID, owner, memory usage (in % of available
RAM), used CPU time, full command line
* Output should be in table format just like `top` or `ps`.
* Output should be truncated at the rightmost column of the terminal window
* Output should be sorted by `score`, with `score` being `(used CPU time) *
(memory usage)`. The intention here is to put the most interesting processes on
top.
* Each column should be wide enough to fit its widest value
* Add a section about installation instructions to this document.
* Add making-a-release instructions to this document
* Add a `.travis.yml` config to the project that:
  * OK: Runs `flake8` on the code
  * OK: Tests the code on OS X
  * OK: Tests the code on Linux
* When piping to some other command, don't truncate lines to terminal width
* If we get one command line argument, only show processes matching that string
as either a user or the name of an executable.
* If we get something looking like a PID as a command line argument, show that
PID process in a tree with all parents up to the top and all children down. This
would replace `pstree`.
* If we get something looking like a PID as a command line argument, for that
PID show:
 * A list of all open files, pipes and sockets
 * For each pipe / domain socket, print the process at the other end
 * For each socket, print where it's going
* Doing `px --version` prints a `git describe` version string.
* Add a column with the name of each running process
* Put column headings at the top of each column
* In the details view, list processes as `Name(PID)` rather than `PID:Name`.
To humans the name is more important than the PID, so it should be first.
* In the details view, list a number of processes that were created around the
same time as the one we're currently looking at.
* Implement support for `px --top`
* If the user launches `px` through a symlink that's called something ending in
`top`, enter `top` mode.
* top: On pressing "q" to exit, redraw the screen one last time with a few less
rows than usual before exiting.
* top: Print system load before the process listing.
* Parse Java and Python command lines and print the name of the program being
executed rather than the VM.
* In the details view, list users that were logged in when the process was
started.
* In the details tree view, print process owners for each line
* Print $SUDO_USER value with process details, if set
