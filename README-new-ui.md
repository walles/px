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
  - FIXME: Unclear
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
