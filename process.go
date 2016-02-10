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
	cpuTimeSeconds      float64
	memoryPercentString string
	memoryPercent       float32
	score               float64
	name                string
	cmdline             string
}

// ByRelevance orders processes by how interesting they are
type ByRelevance []*Process

func (p ByRelevance) Len() int      { return len(p) }
func (p ByRelevance) Swap(i, j int) { p[i], p[j] = p[j], p[i] }
func (p ByRelevance) Less(i, j int) bool {
	if p[i].score < p[j].score {
		return true
	}
	if p[i].score > p[j].score {
		return false
	}

	if p[i].memoryPercent < p[j].memoryPercent {
		return true
	}
	if p[i].memoryPercent > p[j].memoryPercent {
		return false
	}

	if p[i].cpuTimeSeconds < p[j].cpuTimeSeconds {
		return true
	}
	if p[i].cpuTimeSeconds > p[j].cpuTimeSeconds {
		return false
	}

	if p[i].name < p[j].name {
		return true
	}
	if p[i].name > p[j].name {
		return false
	}

	return p[i].cmdline < p[j].cmdline
}

// NewProcess creates a new Process based on a psutil Process object
func NewProcess(proc *process.Process) *Process {
	// FIXME: proc.Username() returns 'root' even for non-root processes
	user, err := proc.Username()
	if err != nil {
		user = "--"
	}

	cpuTimeString := "--"
	var cpuTimeSeconds float64
	cpuTime, err := proc.CPUTimes()
	if err == nil {
		cpuTimeSeconds = cpuTime.Total()
		cpuTimeString = fmt.Sprintf("%.3fs", cpuTimeSeconds)
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
		cpuTimeSeconds:      cpuTimeSeconds,
		memoryPercentString: memoryPercentString,
		memoryPercent:       memoryPercent,
		score:               cpuTimeSeconds * float64(memoryPercent),
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
