package main

import (
	"fmt"

	"github.com/shirou/gopsutil/process"
)

func main() {
	pids, _ := process.Pids()

	fmt.Println(pids)
}
