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

func main() {
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
		name, _ := proc.Name()

		// cmdline, _ := proc.Cmdline()

		fmt.Printf("%d %s %s %s %s\n", pid, user, cpuTimeString, memoryPercentString, name)
	}
}
