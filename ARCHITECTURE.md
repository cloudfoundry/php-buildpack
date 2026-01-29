# PHP Buildpack Architecture

This document explains the architecture of the Cloud Foundry PHP buildpack, with particular focus on why it differs from other Cloud Foundry buildpacks (Go, Ruby, Python, Node.js).

## Table of Contents

- [Overview](#overview)
- [Why PHP is Different](#why-php-is-different)
- [Buildpack Lifecycle](#buildpack-lifecycle)
- [Runtime Architecture](#runtime-architecture)
- [Pre-compiled Binaries](#pre-compiled-binaries)
- [Template Rewriting System](#template-rewriting-system)
- [Process Management](#process-management)
- [Extensions System](#extensions-system)
- [Comparison with Other Buildpacks](#comparison-with-other-buildpacks)

## Overview

The PHP buildpack uses a **hybrid architecture** that combines:

1. **Bash wrapper scripts** for buildpack lifecycle hooks (detect, supply, finalize, release)
2. **Go implementations** for core logic (compiled at staging time)
3. **Pre-compiled runtime utility** for application startup (start)

This design optimizes for both flexibility during staging and performance at runtime.

## Why PHP is Different

Unlike Go, Ruby, Python, or Node.js applications, PHP applications require a **multi-process architecture**:

```
┌─────────────────────────────────────────┐
│         PHP Application                  │
├─────────────────────────────────────────┤
│  ┌────────────┐      ┌──────────────┐  │
│  │ PHP-FPM    │◄────►│ Web Server   │  │
│  │ (FastCGI)  │ TCP  │ (httpd/nginx)│  │
│  │ Port 9000  │      │              │  │
│  └────────────┘      └──────────────┘  │
│        ▲                    ▲           │
│        │                    │           │
│        └────────┬───────────┘           │
│                 │                       │
│          Process Manager                │
│        ($HOME/.bp/bin/start)            │
└─────────────────────────────────────────┘
```

**Key differences from other languages:**

| Language | Architecture | Startup Command |
|----------|-------------|-----------------|
| Go | Single process | `./my-app` |
| Ruby | Single process (Puma/Unicorn) | `bundle exec rails s` |
| Python | Single process (Gunicorn) | `gunicorn app:app` |
| Node.js | Single process | `node server.js` |
| **PHP** | **Two processes** | **`.bp/bin/start` (manager)** |

PHP requires:
1. **PHP-FPM** - Executes PHP code via FastCGI protocol
2. **Web Server** - Serves static files, proxies PHP requests to PHP-FPM

## Buildpack Lifecycle

### 1. Detect Phase (`bin/detect`)

Bash wrapper that compiles and runs `src/php/detect/cli/main.go`:

```bash
#!/bin/bash
# Compiles Go code at staging time
GOROOT=$GoInstallDir $GoInstallDir/bin/go build -o $output_dir/detect ./src/php/detect/cli
$output_dir/detect "$BUILD_DIR"
```

**Why bash wrapper?**
- Allows on-the-fly compilation with correct Go version
- No pre-built binaries needed for different platforms
- Simpler maintenance (one codebase for all platforms)

### 2. Supply Phase (`bin/supply`)

Installs dependencies:
- PHP runtime
- Web server (httpd or nginx)
- PHP extensions
- Composer (if needed)

**Location:** `src/php/supply/supply.go`

### 3. Finalize Phase (`bin/finalize`)

Configures the application for runtime:
- Processes configuration files to replace build-time placeholders with runtime values
- Generates start scripts with correct paths
- Copies `start` binary to `$HOME/.bp/bin/`
- Sets up environment variables

**Location:** `src/php/finalize/finalize.go`

Key code (finalize.go:160-212):
```go
func (f *Finalizer) CreateStartScript(depsIdx string) error {
    // Read WEB_SERVER from options.json
    opts, _ := options.LoadOptions(buildDir)
    
    switch opts.WebServer {
    case "nginx":
        startScript = f.generateNginxStartScript(depsIdx, opts)
    case "httpd":
        startScript = f.generateHTTPDStartScript(depsIdx, opts)
    case "none":
        startScript = f.generatePHPFPMStartScript(depsIdx, opts)
    }
    
    // Write to $DEPS_DIR/0/start_script.sh
    os.WriteFile(startScriptPath, []byte(startScript), 0755)
}
```

### 4. Release Phase (`bin/release`)

Outputs the default process type:

```yaml
default_process_types:
  web: $HOME/.bp/bin/start
```

**Location:** `src/php/release/cli/main.go`

## Runtime Architecture

When a PHP application starts, Cloud Foundry runs:

```bash
$HOME/.bp/bin/start
```

This triggers the following sequence:

```
1. Cloud Foundry
   └─► $HOME/.bp/bin/start
       │
       ├─► Load .procs file
       │   (defines processes to run)
       │
       ├─► Handle dynamic runtime variables
       │   (PORT, TMPDIR via sed replacement)
       │
       ├─► Start PHP-FPM
       │   (background, port 9000)
       │
       ├─► Start Web Server
       │   (httpd or nginx)
       │
       └─► Monitor both processes
           (multiplex output, handle failures)
```

## Pre-compiled Binary

The buildpack includes a pre-compiled runtime utility:

### Why Pre-compiled?

Unlike lifecycle hooks (detect, supply, finalize) which run **during staging**, this utility runs **during application startup**. Pre-compilation provides:

1. **Fast startup time** - No compilation delay when starting the app
2. **Reliability** - Go toolchain not available in runtime container
3. **Simplicity** - Single binary, no dependencies

### `bin/start` (1.9 MB)

**Purpose:** Multi-process manager

**Source:** `src/php/start/cli/main.go`

**Why needed:** PHP requires coordinated management of two processes (PHP-FPM + Web Server) with:
- Output multiplexing (combined logs)
- Lifecycle management (start both, stop if one fails)
- Signal handling (graceful shutdown)
- Process monitoring

**How it works:**

```go
// 1. Load process definitions from $HOME/.procs
procs, err := loadProcesses("$HOME/.procs")
// Format: name: command
// php-fpm: $DEPS_DIR/0/start_script.sh

// 2. Create process manager
pm := NewProcessManager()
for name, cmd := range procs {
    pm.AddProcess(name, cmd)
}

// 3. Start all processes
pm.Start()

// 4. Multiplex output with timestamps
// 14:23:45 php-fpm  | Starting PHP-FPM...
// 14:23:46 httpd    | Starting Apache...

// 5. Monitor for failures
// If any process exits, shutdown all and exit
pm.Loop()
```

**Process file format** (`$HOME/.procs`):

```
# Comments start with #
process-name: shell command to run

# Example:
php-fpm: $DEPS_DIR/0/start_script.sh
```

**Signal handling:**
- `SIGTERM`, `SIGINT` → Graceful shutdown of all processes
- Child process exits → Shutdown all and exit with same code

## Template Rewriting System

The buildpack uses a sophisticated template system to handle runtime configuration:

### Why Templates?

Cloud Foundry provides **runtime-assigned values**:

```bash
# Assigned by Cloud Foundry when container starts
export PORT=8080              # HTTP port (random)
export HOME=/home/vcap/app    # Application directory
export DEPS_DIR=/home/vcap/deps  # Dependencies directory
```

These values **cannot be known at staging time**, so configuration files use templates:

### Template Syntax

| Pattern | Description | Example |
|---------|-------------|---------|
| `@{VAR}` | Braced @ syntax | `@{PORT}` → `8080` |
| `#{VAR}` | Braced # syntax | `#{HOME}` → `/home/vcap/app` |
| `@VAR@` | @ delimited | `@WEBDIR@` → `htdocs` |
| `#VAR` | # prefix (word boundary) | `#PHPRC` → `/home/vcap/deps/0/php/etc` |

### Common Template Variables

| Variable | Description | Example Value |
|----------|-------------|---------------|
| `PORT` | HTTP listen port | `8080` |
| `HOME` | Application root | `/home/vcap/app` |
| `WEBDIR` | Web document root | `htdocs` |
| `LIBDIR` | Library directory | `lib` |
| `PHP_FPM_LISTEN` | PHP-FPM socket | `127.0.0.1:9000` |
| `PHPRC` | PHP config dir | `/home/vcap/deps/0/php/etc` |

### Configuration Flow

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Staging Time (supply phase)                               │
│    - Copy template configs with @{PORT}, #{HOME}, etc.       │
│    - Placeholders remain in config files                     │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Finalize Phase (build-time processing)                    │
│    - Replace build-time placeholders with known values       │
│    - Process PHP, PHP-FPM, and web server configs            │
│    - Dynamic runtime values (PORT, TMPDIR) handled via sed   │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Runtime (start script)                                     │
│    - Export environment variables (PORT, TMPDIR, etc.)        │
│    - Use sed to replace remaining dynamic variables          │
│    - Configs now have actual values instead of templates     │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. Start Processes                                            │
│    - PHP-FPM reads php-fpm.conf (with real PORT)             │
│    - Web server reads config (with real HOME, WEBDIR)        │
└──────────────────────────────────────────────────────────────┘
```

### Example: nginx.conf Template

**At staging time** (`defaults/config/nginx/nginx.conf`):

```nginx
server {
    listen @{PORT};
    root #{HOME}/@WEBDIR@;
    
    location ~ \.php$ {
        fastcgi_pass #{PHP_FPM_LISTEN};
    }
}
```

**At finalize/runtime** (after placeholder replacement with `PORT=8080`, `HOME=/home/vcap/app`, `WEBDIR=htdocs`, `PHP_FPM_LISTEN=127.0.0.1:9000`):

```nginx
server {
    listen 8080;
    root /home/vcap/app/htdocs;
    
    location ~ \.php$ {
        fastcgi_pass 127.0.0.1:9000;
    }
}
```

## Process Management

The `start` binary implements a sophisticated process manager:

### Features

1. **Multi-process coordination**
   - Start processes in defined order
   - Monitor all processes
   - Shutdown all if any fails

2. **Output multiplexing**
   - Combine stdout/stderr from all processes
   - Add timestamps and process names
   - Aligned formatting

3. **Signal handling**
   - Forward signals to all child processes
   - Graceful shutdown on SIGTERM/SIGINT
   - Exit with appropriate code

4. **Failure detection**
   - Monitor process exit codes
   - Immediate shutdown if critical process fails
   - Propagate exit code to Cloud Foundry

### Output Format

```
14:23:45 php-fpm  | [08-Jan-2025 14:23:45] NOTICE: fpm is running, pid 42
14:23:45 php-fpm  | [08-Jan-2025 14:23:45] NOTICE: ready to handle connections
14:23:46 httpd    | [Wed Jan 08 14:23:46.123] [mpm_event:notice] [pid 43] AH00489: Apache/2.4.54 configured
14:23:46 httpd    | [Wed Jan 08 14:23:46.456] [core:notice] [pid 43] AH00094: Command line: 'httpd -D FOREGROUND'
```

### Process Manager Implementation

**Location:** `src/php/start/cli/main.go`

Key components:

```go
type ProcessManager struct {
    processes []*Process       // Managed processes
    mu        sync.Mutex       // Thread safety
    wg        sync.WaitGroup   // Process coordination
    done      chan struct{}    // Shutdown signal
    exitCode  int              // Final exit code
}

// Main loop
func (pm *ProcessManager) Loop() int {
    // Start all processes
    pm.Start()
    
    // Setup signal handlers
    sigChan := make(chan os.Signal, 1)
    signal.Notify(sigChan, syscall.SIGTERM, syscall.SIGINT)
    
    // Wait for signal or process failure
    select {
    case sig := <-sigChan:
        pm.Shutdown(sig)
    case <-pm.done:
        // A process exited
    }
    
    return pm.exitCode
}
```

## Extensions System

The buildpack uses an extensions architecture for optional functionality:

### Core Extensions

Located in `src/php/extensions/`:

- **composer** - Manages PHP dependencies via Composer
- **dynatrace** - Application performance monitoring
- **newrelic** - Application monitoring and analytics

### Extension Lifecycle

Extensions hook into buildpack phases:

```go
type Extension interface {
    // Called during supply phase
    Supply(stager libbuildpack.Stager) error
    
    // Called during finalize phase
    Finalize(stager libbuildpack.Stager) error
}
```

**Example:** Composer Extension (`src/php/extensions/composer/composer.go`)

```go
func (c *ComposerExtension) Supply(stager libbuildpack.Stager) error {
    // 1. Check if composer.json exists
    if !fileExists("composer.json") {
        return nil
    }
    
    // 2. Install composer.phar
    if err := c.installComposer(); err != nil {
        return err
    }
    
    // 3. Run composer install
    cmd := exec.Command("php", "composer.phar", "install", "--no-dev")
    return cmd.Run()
}
```

## Comparison with Other Buildpacks

### Go Buildpack

```yaml
# Go is simple: single binary
default_process_types:
  web: ./my-go-app
```

**No need for:**
- Multi-process management
- Runtime configuration templating
- Pre-compiled utilities

### Ruby Buildpack

```yaml
# Ruby uses single application server
default_process_types:
  web: bundle exec puma -C config/puma.rb
```

**Similar to Go:** Single process, no web server separation

### Python Buildpack

```yaml
# Python uses WSGI server
default_process_types:
  web: gunicorn app:app
```

**Similar to Go/Ruby:** Single process model

### PHP Buildpack (This Buildpack)

```yaml
# PHP requires process manager
default_process_types:
  web: $HOME/.bp/bin/start
```

**Unique requirements:**
- ✅ Multi-process coordination (PHP-FPM + Web Server)
- ✅ Runtime configuration templating (PORT assigned at runtime)
- ✅ Pre-compiled utilities (rewrite, start)
- ✅ Complex lifecycle management

### Architectural Comparison Table

| Feature | Go | Ruby | Python | PHP |
|---------|----|----|--------|-----|
| Process count | 1 | 1 | 1 | **2** |
| Process manager | ❌ | ❌ | ❌ | ✅ |
| Runtime templating | ❌ | ❌ | ❌ | ✅ |
| Pre-compiled utilities | ❌ | ❌ | ❌ | ✅ |
| Web server | Built-in | Built-in | Built-in | **Separate** |
| FastCGI | ❌ | ❌ | ❌ | ✅ |

## Development and Debugging

### Building the Buildpack

```bash
# Build Go binaries
./scripts/build.sh

# Package buildpack
./scripts/package.sh --uncached

# Run tests
./scripts/unit.sh
./scripts/integration.sh
```

### Testing Locally

```bash
# Set up test environment
export BUILD_DIR=/tmp/test-build
export CACHE_DIR=/tmp/test-cache
export DEPS_DIR=/tmp/test-deps
export DEPS_IDX=0

mkdir -p $BUILD_DIR $CACHE_DIR $DEPS_DIR/0

# Copy test fixture
cp -r fixtures/default/* $BUILD_DIR/

# Run buildpack phases
./bin/detect $BUILD_DIR
./bin/supply $BUILD_DIR $CACHE_DIR $DEPS_DIR $DEPS_IDX
./bin/finalize $BUILD_DIR $CACHE_DIR $DEPS_DIR $DEPS_IDX

# Check generated files
cat $DEPS_DIR/0/start_script.sh
ls -la $BUILD_DIR/.bp/bin/
```

### Debugging Runtime Issues

```bash
# Enable debug logging in start script
export BP_DEBUG=true

# Start script will output:
# - set -ex (verbose execution)
# - Binary existence checks
# - Environment variables
# - Process startup logs
```

### Modifying Start Binary

```bash
# Edit source
vim src/php/start/cli/main.go

# Rebuild binary
cd src/php/start/cli
go build -o ../../../../bin/start

# Test changes
./scripts/integration.sh
```

## Summary

The PHP buildpack's unique architecture is driven by PHP's multi-process nature:

1. **Multi-process requirement** - PHP-FPM + Web Server (unlike Go/Ruby/Python single process)
2. **Build-time configuration processing** - Most placeholders replaced during finalize phase
3. **Runtime variable handling** - Dynamic values (PORT, TMPDIR) handled via sed at startup
4. **Process coordination** - Two processes must start, run, and shutdown together
5. **Pre-compiled utility** - Fast startup, no compilation during app start

This architecture ensures PHP applications run reliably and efficiently in Cloud Foundry while maintaining compatibility with standard PHP deployment patterns.

## References

- [Cloud Foundry Buildpack Documentation](https://docs.cloudfoundry.org/buildpacks/)
- [PHP-FPM Documentation](https://www.php.net/manual/en/install.fpm.php)
- [Apache mod_proxy_fcgi](https://httpd.apache.org/docs/current/mod/mod_proxy_fcgi.html)
- [Nginx FastCGI](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html)
