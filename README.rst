|Build Status| |Coverage Status|

``ps`` and ``top`` for Human Beings
===================================

Installation
------------
For a standalone install, copy / paste this command into a terminal::

  curl -Ls https://github.com/walles/px/raw/python/install.sh | bash

Or you can install from Pypi::

  sudo pip install --upgrade pxpx

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

Output
======

``px``
-------------
Running just ``px`` lists all running processes, with the most interesting ones last.
Output truncated for brevity.

::

  PID   COMMAND                         USERNAME            CPU RAM COMMANDLINE
      0 kernel                          root                 --  -- kernel PID 0
    116 KernelEventAgent                root              0.01s  0% /usr/sbin/KernelEventAgent
    426 corestoragehelperd              root              0.05s  0% corestoragehelperd
    808 PluginXPCService                johan             0.05s  0% /System/Library/PrivateFrameworks/StoreXPCServices.framework/Versions/A/XPCServices/com.apple.appsto
  ...
  80678 -fish                           johan             0.25s  0% -fish
  80490 Google Chrome Helper            johan            14.76s  1% /Applications/Google Chrome.app/Contents/Versions/58.0.3029.110/Google Chrome Helper.app/Contents/MacOS/Google Chrome Helper --type=renderer --field-trial-handle=1 --lang=sv --enable-offline-auto-reload --enable-offline-auto-reload-visible-only --blink-settings=disallowFetchForDocWrittenScriptsInMainFrame=false,disallowFetchForDocWrittenScriptsInMainFrameOnSlowConnections=false --enable-pinch --num-raster-threads=2 --enable-zero-copy --enable-gpu-memory-buffer-compositor-resources --enable-main-frame-before-activation --content-image-texture-target=0,0,3553;0,1,3553;0,2,3553;0,3,3553;0,4,3553;0,5,3553;0,6,3553;0,7,3553;0,8,3553;0,9,3553;0,10,34037;0,11,34037;0,12,34037;0,13,3553;0,14,3553;0,15,3553;1,0,3553;1,1,3553;1,2,3553;1,3,3553;1,4,3553;1,5,3553;1,6,3553;1,7,3553;1,8,3553;1,9,3553;1,10,34037;1,11,34037;1,12,34037;1,13,3553;1,14,3553;1,15,3553;2,0,3553;2,1,3553;2,2,3553;2,3,3553;2,4,3553;2,5,3553;2,6,3553;2,7,3553;2,8,3553;2,9,3553;2,10,34037;2,11,34037;2,12,34037;2,13,3553;2,14,3553;2,15,3553;3,0,3553;3,1,3553;3,2,3553;3,3,3553;3,4,3553;3,5,34037;3,6,3553;3,7,3553;3,8,3553;3,9,3553;3,10,3553;3,11,3553;3,12,34037;3,13,3553;3,14,34037;3,15,34037;4,0,3553;4,1,3553;4,2,3553;4,3,3553;4,4,3553;4,5,34037;4,6,3553;4,7,3553;4,8,3553;4,9,3553;4,10,3553;4,11,3553;4,12,34037;4,13,3553;4,14,34037;4,15,34037 --disable-accelerated-video-decode --disable-webrtc-hw-vp8-encoding --renderer-client-id=1309
  80729 mdworker                        johan             0.06s  0% /System/Library/Frameworks/CoreServices.framework/Frameworks/Metadata.framework/Versions/A/Support/mdworker -s mdworker -c MDSImporterWorker -m com.apple.mdworker.shared
  80728 AddressBookSourceSync           johan             0.28s  0% /System/Library/Frameworks/AddressBook.framework/Versions/A/Helpers/AddressBookSourceSync.app/Contents/MacOS/AddressBookSourceSync
  80720 GradleWrapperMain               johan              2.6s  1% /usr/bin/java -Xdock:name=Gradle -Xdock:icon=/Users/johan/src/flickr-uploader/FlickrUploaderAndroid/media/gradle.icns -Dorg.gradle.appname=gradlew -classpath /Users/johan/src/flickr-uploader/FlickrUploaderAndroid/gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain build
  80727 GradleDaemon                    johan            25.56s  2% /Library/Java/JavaVirtualMachines/jdk1.8.0_60.jdk/Contents/Home/bin/java -Xmx1536M -Dfile.encoding=UTF-8 -Duser.country=SE -Duser.language=sv -Duser.variant -cp /Users/johan/.gradle/wrapper/dists/gradle-3.5-all/7s64ktr9gh78lhv83n6m1hq9u6/gradle-3.5/lib/gradle-launcher-3.5.jar org.gradle.launcher.daemon.bootstrap.GradleDaemon 3.5

* To give you the most interesting processes close to your next prompt, ``px``
  puts last in its output processes that:

  * Have been started recently (can be seen in the list as high PIDs)

  * Are using lots of memory

  * Have used lots of CPU time

* Java processes are presented as their main class (``GradleDaemon``) rather
  than as their executable (``java``). `This support is available for many VMs`_.

``px java``
-----------
This lists all Java processes. Note how they are presented as their main class
(``GradleDaemon``) rather than as their executable (``java``). `This support is available for many VMs`_.

::

  PID   COMMAND      USERNAME        CPU   RAM COMMANDLINE
  80727 GradleDaemon johan         1m46s  5% /Library/Java/JavaVirtualMachines/jdk1.8.0_60.jdk/Contents/Home/bin/java -Xmx1536M -Dfile.encoding=UTF-8 -Duser.country=SE -Duser.language=sv -Duser.variant -cp /Users/johan/.gradle/wrapper/dists/gradle-3.5-all/7s64ktr9gh78lhv83n6m1hq9u6/gradle-3.5/lib/gradle-launcher-3.5.jar org.gradle.launcher.daemon.bootstrap.GradleDaemon 3.5
  81192 GradleWrapperMain johan    2.57s  1% /usr/bin/java -Xdock:name=Gradle -Xdock:icon=/Users/johan/src/flickr-uploader/FlickrUploaderAndroid/media/gradle.icns -Dorg.gradle.appname=gradlew -classpath /Users/johan/src/flickr-uploader/FlickrUploaderAndroid/gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain build

``px _coreaudiod``
------------------
This lists all processes owned by the ``_coreaudiod`` user.

::

  PID COMMAND      USERNAME       CPU RAM COMMANDLINE
  204 DriverHelper _coreaudiod  6.67s  0% /System/Library/Frameworks/CoreAudio.framework/Versions/A/XPCServices/com.apple.audio.DriverHelper.xpc/Contents/MacOS/com.apple.audio.DriverHelper
  195 coreaudiod   _coreaudiod 43m10s  0% /usr/sbin/coreaudiod

``sudo px 80727``
-----------------
This shows detailed info about PID 80727.

::

  /Library/Java/JavaVirtualMachines/jdk1.8.0_60.jdk/Contents/Home/bin/java
    -Xmx1536M
    -Dfile.encoding=UTF-8
    -Duser.country=SE
    -Duser.language=sv
    -Duser.variant
    -cp
    /Users/johan/.gradle/wrapper/dists/gradle-3.5-all/7s64ktr9gh78lhv83n6m1hq9u6/gradle-3.5/lib/gradle-launcher-3.5.jar
    org.gradle.launcher.daemon.bootstrap.GradleDaemon
    3.5

  kernel(0)                root
    launchd(1)             root
  --> GradleDaemon(80727)  johan

  31m33s ago GradleDaemon was started, at 2017-06-18T13:47:53+02:00.
  7.6% has been its average CPU usage since then, or 2m22s/31m33s

  Other processes started close to GradleDaemon(80727):
    -fish(80678) was started 9.0s before GradleDaemon(80727)
    iTerm2(80676) was started 9.0s before GradleDaemon(80727)
    login(80677) was started 9.0s before GradleDaemon(80727)
    mdworker(80729) was started just after GradleDaemon(80727)
    mdworker(80776) was started 21.0s after GradleDaemon(80727)

  Users logged in when GradleDaemon(80727) started:
    _mbsetupuser
    johan

  2017-06-18T14:19:26.521988: Now invoking lsof, this can take over a minute on a big system...
  2017-06-18T14:19:27.070396: lsof done, proceeding.

  Network connections:
    [IPv6] *:56789 (LISTEN)
    [IPv6] *:62498 (LISTEN)

  Inter Process Communication:
    mDNSResponder(201): [unix] ->0xe32cbd7be6021f1f

  For a list of all open files, do "sudo lsof -p 80727", or "sudo watch lsof -p 80727" for a live view.

* The command line has been split with one argument per line. This makes long
  command lines readable.
* The process tree shows how the Gradle Daemon relates to other processes.
* Details on how long ago Gradle Daemon was started, and how much CPU it has been
  using since.
* A list of other processes started around the same time as Gradle Daemon.
* A list of users logged in when the Gradle Daemon was started.
* A list of network connections the process has open.
* The IPC section shows that the Gradle Daemon is talking to ``mDNSResponder``
  using `Unix domain sockets`_.

The IPC data comes from ``lsof``. ``sudo`` helps ``lsof`` get more detailed
information; the command will work without it but might miss some information.

``ptop``
--------
|ptop screenshot|

* Note how the default sort order of CPU-usage-since-``ptop``-started makes the
  display rather stable.
* Note the system load bar that correlates the system load with the number of
  CPU cores in the system. Green is load handled by physical cores, yellow
  (not shown here) is load handled by hyperthreading cores, and red is load
  over the number of cores.
* Note the fifteen minute load history graph in the load bar. On this system the
  load has been high for the last fifteen minutes. This is a visualization of
  the numbers you get from ``uptime``.
* Note that after you press ``q`` to quit, the display is retained and some
  lines at the bottom are removed to prevent the information you want from
  scrolling out of view.

Development
===========
Note that the build infrastructure here is designed to create a ``px.pex`` file
that works on both Python 2 and Python 3, and on "all" machines with Python
interpreters (tested on Linux and OS X).

* Clone: ``git clone git@github.com:walles/px.git ; cd px``
* Build and test: ``./test.sh``
* Run: ``./px.pex``
* To add dependencies, edit ``requirements.txt``
* To run the same testing that CI does: ``./ci.sh``

Releasing a new Version
-----------------------
1. Consider updating `the Output section`_, push those changes.
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
7. Upload ``pxpx.egg-info/PKG-INFO`` to `the Pypi Package submission page`_.
8. Go to the `pxpx page on Pypi`_ and click the "files" link. Upload ``dist/pxpx-<version>-py2.py3-none-any.whl`` here.

Performance testing
-------------------
* Store the output of ``lsof -F fnaptd0i`` from a big system in lsof.txt.
* ``./tests/benchmark_ipcmap.py lsof.txt``

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

.. _the Output section: #output
.. _download the latest px.pex: https://github.com/walles/px/releases/latest
.. _Unix domain sockets: https://en.wikipedia.org/wiki/Unix_domain_socket
.. _This support is available for many VMs: https://github.com/walles/px/blob/python/tests/px_commandline_test.py
.. _Releases: https://github.com/walles/px/releases
.. _the Pypi Package submission page: https://pypi.python.org/pypi?%3Aaction=submit_form
.. _pxpx page on Pypi: https://pypi.python.org/pypi/pxpx

.. |Build Status| image:: https://travis-ci.org/walles/px.svg?branch=python
   :target: https://travis-ci.org/walles/px
.. |Coverage Status| image:: https://coveralls.io/repos/github/walles/px/badge.svg?branch=python
   :target: https://coveralls.io/github/walles/px?branch=python
.. |ptop screenshot| image:: https://github.com/walles/px/raw/python/ptop-screenshot.gif
