package main

import (
	"fmt"

	"os"
	"os/exec"

	"strconv"

	"strings"

	"github.com/shirou/gopsutil/cpu"
	"github.com/shirou/gopsutil/process"
)

// FIXME: This function is simply copied from process.totalCpuTime. It would be
// better if this was exported so that we could just call it.
func totalCPUTime(t *cpu.CPUTimesStat) float64 {
	total := t.User + t.System + t.Nice + t.Iowait + t.Irq + t.Softirq + t.Steal +
		t.Guest + t.GuestNice + t.Idle
	return total
}

// Get a printf() format truncating a string at terminal width
func getLineFormat() string {
	cmd := exec.Command("stty", "size")
	cmd.Stdin = os.Stdin
	out, err := cmd.Output()
	if err != nil {
		// stty failed
		return "%s\n"
	}

	width, err :=
		strconv.Atoi(strings.Split(strings.TrimSpace(string(out)), " ")[1])
	if err != nil {
		// Unexpected output from stty
		return "%s\n"
	}

	return fmt.Sprintf("%%.%ds\n", width)
}

// FIXME: This program is terribly slow (on OS X). Listing all processes takes
// over 3s. Doing the same thing with ps takes 0.05s on the same machine.
func main() {
	// FIXME: process.Pids doesn't list PID 0 (init)
	pids, _ := process.Pids()

	lineFormat := getLineFormat()

	for _, pid := range pids {
		psutilproc, _ := process.NewProcess(pid)
		proc := NewProcess(psutilproc)

		line := fmt.Sprintf("%d %s %s %s %s %s",
			pid, proc.User(), proc.CPUTimeString(), proc.MemoryPercentString(), proc.Name(), proc.Cmdline())
		fmt.Printf(lineFormat, line)
	}
}
