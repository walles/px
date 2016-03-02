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
```
git clone https://github.com/walles/px.git
cd px
./pants binary px
sudo install ./dist/px.pex /usr/local/bin/px
```

# Usage
Just type `px`. That's all there's to it!

# Development
* Clone: `git clone git@github.com:walles/px.git ; cd px`
* Test: `./ci.sh`
* Build: `./pants binary px`. Your distributable binary is now in `dist/px.pex`.
* Run: `./dist/px.pex`
* To run without first doing the build step: `./pants run px`
* To add dependencies, edit `px/requirements.txt` and `px/BUILD`

# Releasing a new Version
1. Do `git tag` and think about what the next version number should be.
2. Do ```git tag --annotate 1.2.3``` to set the next version number. The
text you write for this tag will show up as the release description on Github,
write something nice!
3. `git push --tags`

# TODO Continuous Integration
Add a `.travis.yml` config to the project that:
* OK: Runs `flake8` on the code
* Tests the code on OS X
* OK: Tests the code on Linux
* NO: Can or should Travis create binaries for us? Think about security vs
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

# TODO Misc
* There should be a `--long` / `-l` option for showing full command lines rather
than truncating at terminal window width
* The init process on OS X has no command line. We should try just listing the
`exe` in that case.
* On insufficient privileges, print a warning to stderr about this and how to
fix it. Note that just [suid-ing `px.pex` won't
work](http://www.faqs.org/faqs/unix-faq/faq/part4/section-7.html), so this point
may require some research.
* When piping to some other command, don't truncate lines to terminal width

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
