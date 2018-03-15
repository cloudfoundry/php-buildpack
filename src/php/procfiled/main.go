package main

import (
	"fmt"
	"os"
	"os/exec"
	"syscall"

	"github.com/cloudfoundry/libbuildpack"
)

func main() {
	if len(os.Args) != 2 {
		panic("Usage: procfiled [PROCFILE]")
	}
	procfile := make(map[string]string)
	if err := libbuildpack.NewYAML().Load(os.Args[1], &procfile); err != nil {
		panic(err)
	}

	procs := make(map[string]*exec.Cmd)
	for k, v := range procfile {
		cmd := exec.Command("sh", "-c", v)
		cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		procs[k] = cmd
	}

	done := make(chan int, 1)
	for k, cmd := range procs {
		go func(k string, cmd *exec.Cmd) {
			if err := cmd.Run(); err != nil {
				if exitError, ok := err.(*exec.ExitError); ok {
					ws := exitError.Sys().(syscall.WaitStatus)
					fmt.Printf("Exit: %s == %d\n", k, ws.ExitStatus())
					done <- ws.ExitStatus()
				}
			}
			done <- 0
		}(k, cmd)
	}
	exitCode := <-done
	for _, cmd := range procs {
		if cmd.Process != nil {
			syscall.Kill(-cmd.Process.Pid, syscall.SIGKILL)
		}
	}
	os.Exit(exitCode)
}
