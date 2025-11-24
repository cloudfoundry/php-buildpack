package main

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"strings"
	"sync"
	"syscall"
	"time"
)

// Process represents a managed process
type Process struct {
	Name    string
	Command string
	Cmd     *exec.Cmd
	ctx     context.Context
	cancel  context.CancelFunc
}

// ProcessManager manages multiple processes
type ProcessManager struct {
	processes []*Process
	mu        sync.Mutex
	wg        sync.WaitGroup
	done      chan struct{}
	exitCode  int
}

// NewProcessManager creates a new process manager
func NewProcessManager() *ProcessManager {
	return &ProcessManager{
		processes: make([]*Process, 0),
		done:      make(chan struct{}),
	}
}

// AddProcess adds a process to be managed
func (pm *ProcessManager) AddProcess(name, command string) {
	ctx, cancel := context.WithCancel(context.Background())
	proc := &Process{
		Name:    name,
		Command: command,
		ctx:     ctx,
		cancel:  cancel,
	}
	pm.processes = append(pm.processes, proc)
	log.Printf("Adding process [%s] with cmd [%s]", name, command)
}

// Start starts all managed processes
func (pm *ProcessManager) Start() error {
	for _, proc := range pm.processes {
		if err := pm.startProcess(proc); err != nil {
			return fmt.Errorf("failed to start process %s: %w", proc.Name, err)
		}
	}
	return nil
}

// startProcess starts a single process
func (pm *ProcessManager) startProcess(proc *Process) error {
	// Create command with shell
	proc.Cmd = exec.CommandContext(proc.ctx, "bash", "-c", proc.Command)

	// Get stdout/stderr pipes
	stdout, err := proc.Cmd.StdoutPipe()
	if err != nil {
		return fmt.Errorf("failed to create stdout pipe: %w", err)
	}

	stderr, err := proc.Cmd.StderrPipe()
	if err != nil {
		return fmt.Errorf("failed to create stderr pipe: %w", err)
	}

	// Start the process
	if err := proc.Cmd.Start(); err != nil {
		return fmt.Errorf("failed to start command: %w", err)
	}

	log.Printf("Started [%s] with pid [%d]", proc.Name, proc.Cmd.Process.Pid)

	// Read output in goroutines
	pm.wg.Add(2)
	go pm.readOutput(proc, stdout)
	go pm.readOutput(proc, stderr)

	// Monitor process completion
	pm.wg.Add(1)
	go pm.monitorProcess(proc)

	return nil
}

// readOutput reads and prints output from a process
func (pm *ProcessManager) readOutput(proc *Process, reader io.Reader) {
	defer pm.wg.Done()

	scanner := bufio.NewScanner(reader)
	for scanner.Scan() {
		line := scanner.Text()
		timestamp := time.Now().Format("15:04:05")

		// Calculate width for alignment (use max width of process names)
		width := 0
		for _, p := range pm.processes {
			if len(p.Name) > width {
				width = len(p.Name)
			}
		}

		// Print with prefix: "HH:MM:SS name | line"
		fmt.Printf("%s %-*s | %s\n", timestamp, width, proc.Name, line)
	}
}

// monitorProcess monitors a process and handles completion
func (pm *ProcessManager) monitorProcess(proc *Process) {
	defer pm.wg.Done()

	err := proc.Cmd.Wait()

	pm.mu.Lock()
	defer pm.mu.Unlock()

	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			log.Printf("process [%s] with pid [%d] terminated with exit code %d",
				proc.Name, proc.Cmd.Process.Pid, exitErr.ExitCode())
			if pm.exitCode == 0 {
				pm.exitCode = exitErr.ExitCode()
			}
		} else {
			log.Printf("process [%s] with pid [%d] terminated with error: %v",
				proc.Name, proc.Cmd.Process.Pid, err)
			if pm.exitCode == 0 {
				pm.exitCode = 1
			}
		}
	} else {
		log.Printf("process [%s] with pid [%d] terminated",
			proc.Name, proc.Cmd.Process.Pid)
	}

	// If one process exits, terminate all others
	select {
	case <-pm.done:
		// Already terminating
	default:
		close(pm.done)
		pm.terminateAll()
	}
}

// terminateAll terminates all processes
func (pm *ProcessManager) terminateAll() {
	log.Println("sending SIGTERM to all processes")

	for _, proc := range pm.processes {
		if proc.Cmd != nil && proc.Cmd.Process != nil {
			// Check if process is still running
			if err := proc.Cmd.Process.Signal(syscall.Signal(0)); err == nil {
				log.Printf("sending SIGTERM to pid [%d]", proc.Cmd.Process.Pid)
				proc.Cmd.Process.Signal(syscall.SIGTERM)
			}
		}
	}

	// Wait up to 5 seconds, then send SIGKILL
	go func() {
		time.Sleep(5 * time.Second)
		for _, proc := range pm.processes {
			if proc.Cmd != nil && proc.Cmd.Process != nil {
				// Check if process is still running
				if err := proc.Cmd.Process.Signal(syscall.Signal(0)); err == nil {
					log.Printf("sending SIGKILL to pid [%d]", proc.Cmd.Process.Pid)
					proc.Cmd.Process.Kill()
				}
			}
		}
	}()
}

// Loop runs the main event loop
func (pm *ProcessManager) Loop() int {
	// Start all processes
	if err := pm.Start(); err != nil {
		fmt.Fprintf(os.Stderr, "Error starting processes: %v\n", err)
		return 1
	}

	// Handle signals
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	go func() {
		sig := <-sigChan
		log.Printf("Received signal: %v", sig)
		pm.mu.Lock()
		if pm.exitCode == 0 {
			pm.exitCode = 130 // Standard exit code for SIGINT
		}
		pm.mu.Unlock()

		select {
		case <-pm.done:
			// Already terminating
		default:
			close(pm.done)
			pm.terminateAll()
		}
	}()

	// Wait for completion
	pm.wg.Wait()

	return pm.exitCode
}

// loadProcesses loads process definitions from a file
func loadProcesses(path string) (map[string]string, error) {
	log.Printf("Loading processes from [%s]", path)

	file, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("failed to open process file: %w", err)
	}
	defer file.Close()

	procs := make(map[string]string)
	scanner := bufio.NewScanner(file)

	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		// Split on first colon
		parts := strings.SplitN(line, ":", 2)
		if len(parts) != 2 {
			log.Printf("Warning: skipping invalid line: %s", line)
			continue
		}

		name := strings.TrimSpace(parts[0])
		cmd := strings.TrimSpace(parts[1])
		procs[name] = cmd
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("error reading process file: %w", err)
	}

	log.Printf("Loaded processes: %v", procs)
	return procs, nil
}

func main() {
	// Setup logging to file
	logDir := "logs"
	if err := os.MkdirAll(logDir, 0755); err != nil {
		fmt.Fprintf(os.Stderr, "Warning: failed to create logs directory: %v\n", err)
	}

	logFile, err := os.OpenFile(filepath.Join(logDir, "proc-man.log"),
		os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Warning: failed to open log file: %v\n", err)
	} else {
		defer logFile.Close()
		log.SetOutput(logFile)
		log.SetFlags(log.Ldate | log.Ltime | log.Lmicroseconds)
	}

	// Get HOME directory
	home := os.Getenv("HOME")
	if home == "" {
		fmt.Fprintln(os.Stderr, "Error: HOME environment variable not set")
		os.Exit(1)
	}

	// Load processes from .procs file
	procFile := filepath.Join(home, ".procs")
	procs, err := loadProcesses(procFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error loading processes: %v\n", err)
		os.Exit(1)
	}

	// Setup process manager
	pm := NewProcessManager()
	for name, cmd := range procs {
		pm.AddProcess(name, cmd)
	}

	// Start everything and wait
	os.Exit(pm.Loop())
}
