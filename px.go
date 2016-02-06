package main

import (
	"fmt"

	"github.com/shirou/gopsutil/process"
)

func main() {
	pids, _ := process.Pids()

	for _, pid := range pids {
		fmt.Println(pid)
	}
}
