package main

import (
	"fmt"

	"github.com/shirou/gopsutil/cpu"
	"github.com/shirou/gopsutil/process"
)

// Process is useful for sorting and printing process information
type Process struct {
	pidString           string
	user                string
	cpuTimeString       string
	memoryPercentString string
	name                string
	cmdline             string
}

// FIXME: This function is simply copied from process.totalCpuTime. It would be
// better if this was exported so that we could just call it.
func totalCPUTime(t *cpu.CPUTimesStat) float64 {
	total := t.User + t.System + t.Nice + t.Iowait + t.Irq + t.Softirq + t.Steal +
		t.Guest + t.GuestNice + t.Idle
	return total
}

// NewProcess creates a new Process based on a psutil Process object
func NewProcess(proc *process.Process) *Process {
	// FIXME: proc.Username() returns 'root' even for non-root processes
	user, err := proc.Username()
	if err != nil {
		user = "--"
	}

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

	return &Process{
		pidString:           fmt.Sprintf("%d", proc.Pid),
		user:                user,
		cpuTimeString:       cpuTimeString,
		memoryPercentString: memoryPercentString,
		name:                name,
		cmdline:             cmdline,
	}
}

// PidString returns a string representation of this process' PID
func (p *Process) PidString() string {
	return p.pidString
}

// User returns the username owning this process
func (p *Process) User() string {
	return p.user
}

// CPUTimeString returns a string representation of how much CPU time this
// process has consumed
func (p *Process) CPUTimeString() string {
	return p.cpuTimeString
}

// MemoryPercentString returns a string representation of how much RAM this
// process is using
func (p *Process) MemoryPercentString() string {
	return p.memoryPercentString
}

// Name returns the name of the process. This is most often the name of the
// executable.
func (p *Process) Name() string {
	return p.name
}

// Cmdline returns the command line for this process
func (p *Process) Cmdline() string {
	return p.cmdline
}
