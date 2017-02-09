|Build Status| |Coverage Status|

Cross Functional Process Explorer
=================================

Installation
------------
Copy / paste this command line in a terminal::

  curl -Ls https://github.com/walles/px/raw/python/install.sh | bash

Now, you should be able to run ``px``, ``px --help`` or ``ptop`` from the command
line. Otherwise please verify that ``/usr/local/bin`` is in your ``$PATH``.

To try ``px`` without installing it, just `download the latest px.pex`_,
``chmod a+x px.pex``, then run ``./px.pex``.

Usage
-----
Just type ``px`` or ``ptop``, that's a good start!

To exit ``ptop``, press "``q``".

Also try ``px --help`` to see what else ``px`` can do except for just listing all
processes.

Vision
------
One utility, supporting at least OS X and Linux, replacing

* ✅ ``ps``, but with sensible defaults (just do ``px``)
* ✅ ``pgrep`` (running ``px root`` lists only root's processes,
  running ``px java`` lists only java processes)
* ✅ ``pstree`` (running ``px 1234`` shows PID 1234 in a tree, plus
  other information about that process)
* ✅ ``top``, by running ``px --top``, or starting ``px`` through a
  symlink ending in ``top``. ``ptop`` anyone?
* Possibly ``iotop``

Demo
----
|Screenshot|

This screenshot shows:

* The end of the output from just typing ``px``.

  * Note how the newest and the most CPU and memory hungry processes are at the
    end of the list so you can find them without scrolling.
  * Note how the Gradle daemon processes running in Java is listed by class name
    (``GradleDaemon``) rather than the JVM executable name (``java``).

* The result of searching for "terminal" processes.
* The output from the details view of PID 70857:

  * The command line has been split with one argument per line. This makes long
    command lines readable.
  * The process tree shows how the Terminal relates to other processes.
  * Details on how long ago Terminal was started, and how much CPU it has been
    using since.
  * A list of other processes started around the same time as Terminal.
  * A list of users logged in when the Terminal was started.
  * The IPC section shows that the Terminal is talking to ``launchd`` and
    ``syslogd`` using
    `Unix domain sockets`_.

Development
-----------
* Clone: ``git clone git@github.com:walles/px.git ; cd px``
* Build and test: ``./test.sh``
* Run: ``./px.pex``
* To add dependencies, edit ``requirements.txt``
* To run the same testing that CI does: ``./ci.sh``

Releasing a new Version
-----------------------
1. Consider updating ``screenshot.png`` and `the Demo section`_, push those changes.
2. Do ``git tag`` and think about what the next version number should be.
3. Do ``git tag --annotate 1.2.3`` to set the next version number. The
   text you write for this tag will show up as the release description on Github,
   write something nice! And remember that the first line is the subject line for
   the release.
4. ``./ci.sh``
5. ``git push --tags``
6. Go to the `Releases`_ page on GitHub,
   click your new release, click the ``Edit tag`` button, then attach your ``px.pex``
   file that you just built to the release.

Performance testing
-------------------
* Store the output of ``lsof -F fnaptd0i`` from a big system in lsof.txt.
* ``./px/benchmark_ipcmap.py lsof.txt``

Keeping this benchmark performant is important to be able to use ``px`` on big
systems.

TODO ``top`` replacement
------------------------

* Disable terminal line wrapping for smoother handling of terminal window
  resizes.

TODO ``iotop`` replacement
--------------------------

* When given the ``--top`` flag and enough permissions, record per process IO
  usage and present that in one or more columns.

TODO misc
---------

* Details: When no users were found to be logged in at process start,
  automatically detect whether it's because we don't have history that far back or
  whether it seems to be that nobody was actually logged in. Inform the user about
  the outcome.
* In the px / top views, in the process owner column, maybe print other non-root
  process owners of parent processes inside parentheses?
* In the details report, if the current process has a working directory that
  isn't ``/``, list all other processes that have the same working directory.
* Ignore -E switch on Python command lines


DONE
----
* Make ``px`` list all processes with PID, owner, memory usage (in % of available
  RAM), used CPU time, full command line
* Output should be in table format just like ``top`` or ``ps``.
* Output should be truncated at the rightmost column of the terminal window
* Output should be sorted by ``score``, with ``score`` being ``(used CPU time) *
  (memory usage)``. The intention here is to put the most interesting processes on
  top.
* Each column should be wide enough to fit its widest value
* Add a section about installation instructions to this document.
* Add making-a-release instructions to this document
* Add a ``.travis.yml`` config to the project that:
  * OK: Runs ``flake8`` on the code
  * OK: Tests the code on OS X
  * OK: Tests the code on Linux

* When piping to some other command, don't truncate lines to terminal width
* If we get one command line argument, only show processes matching that string
  as either a user or the name of an executable.
* If we get something looking like a PID as a command line argument, show that
  PID process in a tree with all parents up to the top and all children down. This
  would replace ``pstree``.
* If we get something looking like a PID as a command line argument, for that
  PID show:
  * A list of all open files, pipes and sockets
  * For each pipe / domain socket, print the process at the other end
  * For each socket, print where it's going

* Doing ``px --version`` prints a ``git describe`` version string.
* Add a column with the name of each running process
* Put column headings at the top of each column
* In the details view, list processes as ``Name(PID)`` rather than ``PID:Name``.
  To humans the name is more important than the PID, so it should be first.
* In the details view, list a number of processes that were created around the
  same time as the one we're currently looking at.
* Implement support for ``px --top``
* If the user launches ``px`` through a symlink that's called something ending in
  ``top``, enter ``top`` mode.
* top: On pressing "q" to exit, redraw the screen one last time with a few less
  rows than usual before exiting.
* top: Print system load before the process listing.
* Parse Java and Python command lines and print the name of the program being
  executed rather than the VM.
* In the details view, list users that were logged in when the process was
  started.
* In the details tree view, print process owners for each line
* Print ``$SUDO_USER`` value with process details, if set
* Run CI on both Python 2 and Python 3

.. _the Demo section: #demo
.. _download the latest px.pex: https://github.com/walles/px/releases/latest
.. _Unix domain sockets: https://en.wikipedia.org/wiki/Unix_domain_socket)
.. _Releases: https://github.com/walles/px/releases

.. |Build Status| image:: https://travis-ci.org/walles/px.svg?branch=python
   :target: https://travis-ci.org/walles/px
.. |Coverage Status| image:: https://coveralls.io/repos/github/walles/px/badge.svg?branch=python
   :target: https://coveralls.io/github/walles/px?branch=python
.. |Screenshot| image:: https://raw.githubusercontent.com/walles/px/python/screenshot.png
