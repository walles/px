# Plan for a New `ptop` User Interface

## Use Cases and What Metrics Would Support Them

- Why is my fan making noises?
  - Process top list by CPU usage
- I have a CPU meter that is peaking, why?
  - Process top list by CPU usage
- I have a RAM meter that is peaking, why?
  - Process top list by RAM usage
- Why is my computer slow?
  - Process top list by CPU usage
  - Process top list by RAM usage
  - Process top list by IO usage
- Which processes are IO heavy?
  - Process top list by IO usage
- Is this specific process leaking memory?
  - When a process is selected, replace the user top lists with a braille
    history chart for the current process. This means we need to collect
    historical data for each process.
- Which new processes are being launched and why?
  - The ptop launched-binaries tree is excellent for this
- Is some particular service running?
  - Process search by name or number
- Which users are consuming CPU?
  - User top list by CPU usage
- Which users are consuming RAM?
  - User top list by RAM usage
- Which users are consuming IO?
  - User top list by IO usage
- I want to see the overall system load and resource usage
  - System load graph for CPU.
  - Memory pressure as measured by "system" CPU time. Or some number, since even
    if it doesn't help them, this is the number people expect to see.
  - Some IO load number.
- I need to check if my system is under heavy I/O load
  - Process top list by IO usage
  - Or if that's not possible, device top list by IO usage
- I want to see if a process is stuck or in an uninterruptible sleep state
  - Nah, let's just not care about this until somebody explicitly asks for it
- I need to find and kill a runaway process.
  - Find: Process top list by CPU usage and / or by RAM usage
  - Kill: Select process and provide a way for the user to request its termination
- Why is some process running on my system?
  - The px-for-one-process view is excellent for this

## Metrics we Want to Show

In order of number of use cases they support. For metrics that will go into some particular section, they are prefixed with that section name:

- CPU: Process top list by CPU usage
- RAM: Process top list by RAM usage
- Launched-binaries tree view
- Top lists filtering by (process, device or user) name or number
- IO: Device top list by IO usage. This is possible. Per-process IO usage is
  not.
- CPU: User top list by CPU usage
- RAM: User top list by RAM usage
- User top list by IO usage is not possible. Stick to the device top list ^.
- CPU: Human understandable sysload graph / number(s). Current `ptop` stats are
  nice, use this but possibly reconsider its presentation.
- RAM: Some RAM metric. Either RAM pressure because it's useful or "used RAM"
  because people expect to see it even if it doesn't really help them.
- Some way to select a process and request its termination.
- Some way to select a process and see why it's running. Current `ptop`
  px-for-one-process view is good for this.

## UI Sections and What They Should Contain

- CPU
  - Process top list by CPU usage
  - User top list by CPU usage
  - System load graph / number
- RAM
  - Process top list by RAM usage
  - User top list by RAM usage
  - Some RAM metric. Either RAM pressure or "used RAM"
- IO
  - Device top list by IO usage
- EXE
  - This section will contain the launched-binaries tree view
- Help bar at the bottom with key press hints. Will turn into a filter bar on
  `/`. Filter expressions will filter all visible lists by whatever makes sense
  for that particular list. Name, PID, user, etc.

Apart from this, TAB should be used for activating different sections. Up and
down arrow keys for browsing processes in the current list. Enter for selecting
a process. Once selected you should get options for viewing process info or
killing it.

## Prettiness

`btop` looks nice, take inspiration from there!

To be able to do that, we need:

- Have different color themes, at least one for light and one for dark terminal
  backgrounds
- Enable passing the theme on the command line
- Enable reading the theme from an environment variable
- Auto detect light / dark terminal background on terminals which support that
  and pick the default based on that
- Define our UI in 24 bit color and adapt the actual output to what the terminal
  supports. `btop` looks horrible in macOS Terminal because it only supports 256
  colors.
- Enable passing the terminal color depth on the command line
- Enable reading the terminal color depth from our environment variable
- Auto pick the terminal color depth based on terminal capabilities

Consider having different horizontal sections. On the left, each section could
have vertical labels made of braille characters:

- CPU
- RAM
- IO
- EXE (binaries launched)

## Implementation

First, consider redoing in Go using:

- Twin (from moor) for the terminal UI
- gopsutil for process and system metrics
  - For process info no, seems very slow at listing processes with user names
    compared to just parsing `ps` output.
    - https://github.com/shirou/gopsutil/issues/842
    - https://github.com/shirou/gopsutil/issues/1711
- Do what gotop does for system info / process listing? It uses gopsutil but
  overrides (at least) process listing and uses `ps` instead on not-Windows.

1. Get the UI structure right with plain text only. Verify it works with
   terminal window resizing. Pressing ESC / q should exit.
1. Implement filtering
1. Implement section switching with TAB
1. Implement process picking with arrow keys
1. Implement the I-picked-a-process-by-pressing-enter menu screen
1. Verify we have all Use Cases ^ covered
1. Put the braille section labels in place
1. Color things in 24 bit color
1. Make sure we have two different color themes and the ability to pick. Test
   them on light and dark terminal backgrounds and verify they look OK.
1. Downsample colors to 256 colors and verify it still looks OK
1. Auto pick terminal color depth
1. Make sure we have Prettiness ^ covered
1. Update screenshot(s) in the README
1. Decide on what to do with `px`. It should probably use the same color depth +
   themes logic as `ptop`.
1. Merge into the `python` branch
1. Make a new release.
1. Make sure we are implementing the memory leak use case.
