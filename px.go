package main

import (
	"fmt"

	"github.com/shirou/gopsutil/process"
)

func main() {
	pids, _ := process.Pids()

	for _, pid := range pids {
		proc, _ := process.NewProcess(pid)

		// FIXME: proc.Username() returns 'root' even for non-root processes
		user, _ := proc.Username()

		// cpuTime, _ := proc.CPUTimes()

		// memoryPercent, _ := proc.MemoryPercent()

		// FIXME: proc.Name() is truncated at 16 characters
		name, _ := proc.Name()

		// cmdline, _ := proc.Cmdline()

		fmt.Printf("%d %s %s\n", pid, user, name)
	}
}
