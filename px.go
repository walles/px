package main

import (
	"fmt"

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

// FIXME: This program is terribly slow (on OS X). Listing all processes takes
// over 3s. Doing the same thing with ps takes 0.05s on the same machine.
func main() {
	// FIXME: process.Pids doesn't list PID 0 (init)
	pids, _ := process.Pids()

	for _, pid := range pids {
		proc, _ := process.NewProcess(pid)

		// FIXME: proc.Username() returns 'root' even for non-root processes
		user, _ := proc.Username()

		cpuTimeString := "--"
		cpuTime, err := proc.CPUTimes()
		if err == nil {
			cpuTimeString = fmt.Sprintf("%.3fs", totalCPUTime(cpuTime))
		}

		memoryPercentString := "--"
		// FIXME: proc.MemoryPercent() is "not implemented yet"
		memoryPercent, err := proc.MemoryPercent()
		if err == nil {
			memoryPercentString = fmt.Sprintf("%.1f%%", memoryPercent)
		}

		// FIXME: proc.Name() is truncated at 16 characters
		name, err := proc.Name()
		if err != nil {
			name = "--"
		}

		cmdline, err := proc.Cmdline()
		if err != nil {
			cmdline = "--"
		}

		fmt.Printf("%d %s %s %s %s %s\n", pid, user, cpuTimeString, memoryPercentString, name, cmdline)
	}
}
