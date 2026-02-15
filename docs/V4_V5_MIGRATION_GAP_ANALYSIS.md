# PHP Buildpack v4.x to v5.x Migration Gap Analysis

This document provides a comprehensive comparison between the v4.x (Python) and v5.x (Go) PHP buildpacks, identifying features that are missing, partially implemented, or fully implemented in v5.x.

## Executive Summary

| Category | v4.x Features | v5.x Status | Priority |
|----------|---------------|-------------|----------|
| Core Features | 15 | 15 implemented, 0 missing | Complete |
| Extensions | 5 | 4 implemented, 1 partial | Medium |
| Configuration Options | 25+ | 25+ implemented, 0 missing | Complete |
| Placeholder Syntax | 2 types | Both implemented | Complete |
| Service Bindings | 5 services | 4 implemented | Medium |

---

## Feature Comparison Matrix

### Legend
- ✅ **Implemented** - Feature works in v5.x
- ⚠️ **Partial** - Feature partially implemented or has limitations
- ❌ **Missing** - Feature not implemented in v5.x
- 🔄 **Changed** - Feature behavior changed significantly

---

## 1. Configuration Options

### 1.1 Core Options (options.json)

| Option | v4.x | v5.x | Status | Notes |
|--------|------|------|--------|-------|
| `STACK` | ✅ | ✅ | ✅ | |
| `LIBDIR` | ✅ | ✅ | ✅ | Default: `lib` |
| `WEBDIR` | ✅ | ✅ | ✅ | Default: `htdocs` |
| `WEB_SERVER` | ✅ | ✅ | ✅ | `httpd`, `nginx`, `none` |
| `PHP_VM` | ✅ | ✅ | ✅ | Default: `php` |
| `ADMIN_EMAIL` | ✅ | ✅ | ✅ | Default: `admin@localhost` |
| `PHP_VERSION` | ✅ | ✅ | ✅ | Supports version placeholders |
| `PHP_DEFAULT` | ✅ | ✅ | ✅ | From manifest |
| `PHP_XX_LATEST` | ✅ | ✅ | ✅ | `PHP_81_LATEST`, `PHP_82_LATEST`, `PHP_83_LATEST` |
| `PHP_EXTENSIONS` | ✅ | ✅ | ✅ | Default: `["bz2","zlib","curl"]` |
| `ZEND_EXTENSIONS` | ✅ | ✅ | ✅ | Default: `[]` |
| `PHP_MODULES` | ✅ | ✅ | ✅ | |
| `HTTPD_STRIP` | ✅ | ✅ | ✅ | |
| `NGINX_STRIP` | ✅ | ✅ | ✅ | |
| `PHP_STRIP` | ✅ | ✅ | ✅ | |
| `COMPOSER_VENDOR_DIR` | ✅ | ✅ | ✅ | |
| `COMPOSER_INSTALL_OPTIONS` | ✅ | ✅ | ✅ | |
| `COMPOSER_INSTALL_GLOBAL` | ✅ | ✅ | ✅ | |
| **`ADDITIONAL_PREPROCESS_CMDS`** | ✅ | ✅ | ✅ **IMPLEMENTED** | Commands to run before app starts |
| **`APP_START_CMD`** | ✅ | ✅ | ✅ **IMPLEMENTED** | Custom start command for standalone apps |

### 1.2 Missing Configuration Options - Details

#### `ADDITIONAL_PREPROCESS_CMDS` ✅ IMPLEMENTED

**Status:** Implemented in v5.x (Feb 2026)

**v5.x Implementation:** 
- `src/php/options/options.go` - `GetPreprocessCommands()` method
- `src/php/finalize/finalize.go` - `generatePreprocessCommandsScript()` method

**Supported Formats (same as v4.x):**
```json
// String format
"ADDITIONAL_PREPROCESS_CMDS": "source $HOME/scripts/bootstrap.sh"

// Array format
"ADDITIONAL_PREPROCESS_CMDS": ["env", "run_something"]

// Array of arrays format
"ADDITIONAL_PREPROCESS_CMDS": [["echo", "Hello World"]]
```

**Use Cases:**
- Running database migrations before app starts
- Setting up environment variables via custom scripts
- Initializing cache directories
- Running Drupal drush commands (as reported by user akf in issue #1208)

**Test Fixture:** `fixtures/preprocess_cmds/`

---

#### `APP_START_CMD` ✅ IMPLEMENTED

**Status:** Implemented in v5.x (Feb 2026)

**v5.x Implementation:**
- `src/php/options/options.go` - `APP_START_CMD` field and `FindStandaloneApp()` method
- `src/php/finalize/finalize.go` - `generatePHPFPMStartScript()` modified for standalone mode
- `fixtures/standalone_app/` - Test fixture with explicit APP_START_CMD
- `fixtures/standalone_autodetect/` - Test fixture for auto-detection
- `src/php/integration/standalone_test.go` - Integration tests

**v4.x Reference Implementation:**
```python
def find_stand_alone_app_to_run(ctx):
    app = ctx.get('APP_START_CMD', None)
    if app is None:
        for name in ['app.php', 'main.php', 'run.php', 'start.php']:
            if os.path.exists(os.path.join(ctx['BUILD_DIR'], name)):
                app = name
                break
    if app is None:
        raise RuntimeError('Unable to find stand-alone app to run...')
    return app
```

**Usage:**
```json
{
  "WEB_SERVER": "none",
  "APP_START_CMD": "worker.php"
}
```

**Auto-detection (when `WEB_SERVER=none` and no `APP_START_CMD`):**
1. `app.php`
2. `main.php`
3. `run.php`
4. `start.php`

**Use Cases:**
- Background workers
- Queue processors
- CLI applications
- Scheduled tasks

**Test Fixture:** `fixtures/standalone_app/` and `fixtures/standalone_autodetect/`

**Impact:** MEDIUM - Required for standalone PHP applications (now implemented)

---

## 2. Extensions

### 2.1 Extension Comparison

| Extension | v4.x | v5.x | Status | Notes |
|-----------|------|------|--------|-------|
| **Composer** | ✅ | ✅ | ✅ | Full feature parity |
| **NewRelic** | ✅ | ✅ | ✅ | Full feature parity |
| **AppDynamics** | ✅ | ✅ | ✅ | Full feature parity |
| **Dynatrace** | ✅ | ✅ | ✅ | Uses libbuildpack-dynatrace |
| **Sessions** | ✅ | ✅ | ✅ | Redis + Memcached |
| **User Extensions** | ✅ | ❌ | ❌ **MISSING** | `.extensions/` directory |

### 2.2 Missing Extension Features

#### User/Custom Extensions ❌ CRITICAL

**v4.x Implementation:** `php-buildpack-v4/lib/build_pack_utils/builder.py`

Users could create custom extensions in `.extensions/` directory:

```
app/
├── .extensions/
│   └── my_extension/
│       └── extension.py
├── .bp-config/
│   └── options.json
└── index.php
```

**extension.py interface:**
```python
def configure(ctx):
    """Called during configure phase - set PHP version, extensions, etc."""
    pass

def compile(install):
    """Called during compile phase - install dependencies"""
    pass

def preprocess_commands(ctx):
    """Return list of commands to run before app starts"""
    return []

def service_commands(ctx):
    """Return dict of background services to run"""
    return {}

def service_environment(ctx):
    """Return dict of environment variables"""
    return {}
```

**Use Cases:**
- Custom APM integrations
- Custom service bindings
- Application-specific setup
- Custom PHP extension installation

**Impact:** MEDIUM - Power users rely on this for custom integrations

---

## 3. Placeholder/Variable Substitution

### 3.1 Placeholder Syntax Comparison

| Syntax | v4.x | v5.x | Status | Context |
|--------|------|------|--------|---------|
| `@{VAR}` | ✅ | ✅ | ✅ | Environment variable substitution |
| `#{VAR}` | ✅ | ✅ | ✅ | Context variable substitution (added in 0185dd55e) |
| `{VAR}` | ✅ | ✅ | ✅ | PHP version placeholders only |
| `${VAR}` | ✅ | ✅ | ✅ | Shell expansion at runtime |

### 3.2 Supported Placeholders

| Placeholder | v4.x | v5.x | Context | Notes |
|-------------|------|------|---------|-------|
| `@{HOME}` / `#{HOME}` | ✅ | ✅ | Deps or App | `/home/vcap/deps/{idx}` or `/home/vcap/app` |
| `@{WEBDIR}` / `#{WEBDIR}` | ✅ | ✅ | App | Web root directory |
| `@{LIBDIR}` / `#{LIBDIR}` | ✅ | ✅ | App | Library directory |
| `@{TMPDIR}` / `#{TMPDIR}` | ✅ | ✅ | Runtime | Converted to `${TMPDIR}` |
| `@{PHP_FPM_LISTEN}` / `#{PHP_FPM_LISTEN}` | ✅ | ✅ | PHP | Socket or TCP address |
| `@{ADMIN_EMAIL}` / `#{ADMIN_EMAIL}` | ✅ | ✅ | Web server | Admin email |
| `@{DEPS_DIR}` / `#{DEPS_DIR}` | ✅ | ✅ | PHP | `/home/vcap/deps` |
| `@{PHP_EXTENSIONS}` | ✅ | ✅ | PHP | Extension loading directives |
| `@{ZEND_EXTENSIONS}` | ✅ | ✅ | PHP | Zend extension directives |
| `@{PHP_FPM_CONF_INCLUDE}` | ✅ | ✅ | PHP-FPM | Include directive for fpm.d |
| `{PHP_83_LATEST}` | ✅ | ✅ | Options | Resolved to actual version |
| `{PHP_82_LATEST}` | ✅ | ✅ | Options | Resolved to actual version |
| `{PHP_81_LATEST}` | ✅ | ✅ | Options | Resolved to actual version |

---

## 4. Service Bindings (VCAP_SERVICES)

### 4.1 Service Detection Comparison

| Service | v4.x | v5.x | Status | Detection Pattern |
|---------|------|------|--------|-------------------|
| **NewRelic** | ✅ | ✅ | ✅ | Label: `newrelic` |
| **AppDynamics** | ✅ | ✅ | ✅ | Regex: `app[-]?dynamics` |
| **Dynatrace** | ✅ | ✅ | ✅ | Via libbuildpack-dynatrace |
| **Redis Sessions** | ✅ | ✅ | ✅ | Name contains: `redis-sessions` |
| **Memcached Sessions** | ✅ | ✅ | ✅ | Name contains: `memcached-sessions` |

### 4.2 Environment Variable Overrides

| Variable | v4.x | v5.x | Status | Purpose |
|----------|------|------|--------|---------|
| `NEWRELIC_LICENSE` | ✅ | ✅ | ✅ | Manual license key |
| `REDIS_SESSION_STORE_SERVICE_NAME` | ✅ | ✅ | ✅ | Custom service name trigger |
| `MEMCACHED_SESSION_STORE_SERVICE_NAME` | ✅ | ✅ | ✅ | Custom service name trigger |
| `COMPOSER_GITHUB_OAUTH_TOKEN` | ✅ | ✅ | ✅ | GitHub API authentication |
| `COMPOSER_PATH` | ✅ | ✅ | ✅ | Custom composer.json location |

---

## 5. Web Server Configuration

### 5.1 HTTPD (Apache)

| Feature | v4.x | v5.x | Status |
|---------|------|------|--------|
| Default config | ✅ | ✅ | ✅ |
| User overrides (`.bp-config/httpd/`) | ✅ | ✅ | ✅ |
| mod_proxy_fcgi | ✅ | ✅ | ✅ |
| mod_deflate | ✅ | ✅ | ✅ |
| mod_remoteip | ✅ | ✅ | ✅ |
| PHP-FPM via TCP | ✅ | ✅ | ✅ |

### 5.2 Nginx

| Feature | v4.x | v5.x | Status |
|---------|------|------|--------|
| Default config | ✅ | ✅ | ✅ |
| User overrides (`.bp-config/nginx/`) | ✅ | ✅ | ✅ |
| FastCGI | ✅ | ✅ | ✅ |
| gzip compression | ✅ | ✅ | ✅ |
| PHP-FPM via TCP/Socket | ✅ | ✅ | ✅ |

---

## 6. PHP Configuration

### 6.1 PHP.ini and PHP-FPM

| Feature | v4.x | v5.x | Status |
|---------|------|------|--------|
| Default php.ini | ✅ | ✅ | ✅ |
| User php.ini (`.bp-config/php/php.ini`) | ✅ | ✅ | ✅ |
| php.ini.d directory | ✅ | ✅ | ✅ |
| Default php-fpm.conf | ✅ | ✅ | ✅ |
| User php-fpm.conf | ✅ | ✅ | ✅ |
| fpm.d directory | ✅ | ✅ | ✅ |
| Extension validation | ✅ | ✅ | ✅ |
| Compiled module detection | ✅ | ✅ | ✅ |

### 6.2 Composer Integration

| Feature | v4.x | v5.x | Status |
|---------|------|------|--------|
| Auto-detect composer.json | ✅ | ✅ | ✅ |
| PHP version from composer.json | ✅ | ✅ | ✅ |
| PHP version from composer.lock | ✅ | ✅ | ✅ |
| Extension detection (ext-*) | ✅ | ✅ | ✅ |
| Semver constraint parsing | ✅ | ✅ | ✅ |
| GitHub rate limit detection | ✅ | ✅ | ✅ |
| auth.json support | ✅ | ✅ | ✅ |
| Vendor symlink in WEBDIR | ❌ | ✅ | ✅ | New in v5.x |

---

## 7. Build Process

### 7.1 Build Phases

| Phase | v4.x | v5.x | Status | Notes |
|-------|------|------|--------|-------|
| Detect | ✅ | ✅ | ✅ | |
| Supply | ✅ | ✅ | ✅ | |
| Finalize | ✅ | ✅ | ✅ | |
| Release | ✅ | ✅ | ✅ | |

### 7.2 Multi-Buildpack Support

| Feature | v4.x | v5.x | Status | Notes |
|---------|------|------|--------|-------|
| `000_multi-supply.sh` | ✅ | ✅ | ✅ | Created by libbuildpack |
| PATH setup | ✅ | ✅ | ✅ | |
| LD_LIBRARY_PATH setup | ✅ | ✅ | ✅ | |
| LIBRARY_PATH setup | ✅ | ✅ | ✅ | |
| profile.d scripts | ✅ | ✅ | ✅ | |

---

## 8. Runtime Features

### 8.1 Process Management

| Feature | v4.x | v5.x | Status | Notes |
|---------|------|------|--------|-------|
| PHP-FPM + Web Server | ✅ | ✅ | ✅ | |
| Signal handling | ✅ | ✅ | ✅ | |
| Graceful shutdown | ✅ | ✅ | ✅ | |
| Pre-start script | ❌ | ✅ | ✅ | New in v5.x |
| **Standalone PHP mode** | ✅ | ✅ | ✅ **COMPLETE** | With APP_START_CMD |

### 8.2 Environment Setup

| Feature | v4.x | v5.x | Status |
|---------|------|------|--------|
| PHPRC | ✅ | ✅ | ✅ |
| PHP_INI_SCAN_DIR | ✅ | ✅ | ✅ |
| PATH includes PHP | ✅ | ✅ | ✅ |
| DEPS_DIR fallback | ✅ | ✅ | ✅ |
| TMPDIR customization | ✅ | ✅ | ✅ |

---

## 9. Priority Implementation Roadmap

### 9.1 Completed ✅

| Feature | Effort | Impact | Status |
|---------|--------|--------|--------|
| `ADDITIONAL_PREPROCESS_CMDS` | Medium | HIGH | ✅ Implemented (#1208) |
| `APP_START_CMD` | Low | MEDIUM | ✅ Implemented (Feb 2026) |

### 9.2 High Priority (Remaining)

| Feature | Effort | Impact |
|---------|--------|--------|
| User Extensions (`.extensions/`) | High | MEDIUM |

### 9.3 Nice to Have

| Feature | Effort | Impact |
|---------|--------|--------|
| Additional APM integrations | Medium | LOW |

---

## 10. Implementation Details for Missing Features

### 10.1 ADDITIONAL_PREPROCESS_CMDS Implementation

**Location:** `src/php/options/options.go`

Add to Options struct:
```go
type Options struct {
    // ... existing fields ...
    AdditionalPreprocessCmds interface{} `json:"ADDITIONAL_PREPROCESS_CMDS,omitempty"`
}
```

**Location:** `src/php/finalize/finalize.go`

Add preprocessing logic:
```go
func (f *Finalizer) runAdditionalPreprocessCmds(opts *options.Options) error {
    cmds := opts.GetPreprocessCommands()
    for _, cmd := range cmds {
        f.Log.Info("Running preprocess command: %s", cmd)
        if err := f.Command.Execute(f.Stager.BuildDir(), f.Log.Output(), f.Log.Output(), "bash", "-c", cmd); err != nil {
            return fmt.Errorf("preprocess command failed: %w", err)
        }
    }
    return nil
}
```

**Alternative:** Add to start script for runtime execution (matching v4.x behavior).

### 10.2 APP_START_CMD Implementation

**Location:** `src/php/options/options.go`

Add to Options struct:
```go
type Options struct {
    // ... existing fields ...
    AppStartCmd string `json:"APP_START_CMD,omitempty"`
}
```

**Location:** `src/php/finalize/finalize.go`

Modify `generatePHPFPMStartScript`:
```go
func (f *Finalizer) generatePHPFPMStartScript(depsIdx string, opts *options.Options) string {
    appCmd := opts.AppStartCmd
    if appCmd == "" {
        // Auto-detect: app.php, main.php, run.php, start.php
        for _, name := range []string{"app.php", "main.php", "run.php", "start.php"} {
            if exists, _ := libbuildpack.FileExists(filepath.Join(f.Stager.BuildDir(), name)); exists {
                appCmd = name
                break
            }
        }
    }
    if appCmd == "" {
        return "" // Error: no standalone app found
    }
    
    // Generate script that runs: php $appCmd
    // ...
}
```

### 10.3 User Extensions Implementation

**Location:** `src/php/extensions/user/`

Create user extension loader:
```go
func LoadUserExtensions(buildDir string, registry *Registry) error {
    extensionsDir := filepath.Join(buildDir, ".extensions")
    if exists, _ := libbuildpack.FileExists(extensionsDir); !exists {
        return nil
    }
    
    // For each subdirectory in .extensions/
    // Load extension.py and execute Python methods
    // OR: Define a Go-native extension interface
    // ...
}
```

**Note:** This is complex because v4.x extensions are Python. Options:
1. Keep Python interpreter for user extensions (complex)
2. Define new Go-native extension interface (breaking change)
3. Support shell scripts as extensions (simpler)

---

## 11. Testing Recommendations

### 11.1 Integration Tests Needed

| Test | Status | Priority |
|------|--------|----------|
| ADDITIONAL_PREPROCESS_CMDS - string format | ✅ | HIGH |
| ADDITIONAL_PREPROCESS_CMDS - array format | ✅ | HIGH |
| APP_START_CMD - explicit | ✅ | MEDIUM |
| APP_START_CMD - auto-detect | ✅ | MEDIUM |
| User extensions | ❌ | LOW |
| Multi-buildpack with apt-buildpack | ⚠️ | HIGH |

### 11.2 User Acceptance Testing

Test with real-world applications:
- [ ] Drupal (akf's use case - https://github.com/gsa/digital-gov-drupal)
- [ ] Laravel
- [ ] Symfony
- [ ] WordPress
- [ ] CakePHP

---

## 12. References

- Issue #1208: https://github.com/cloudfoundry/php-buildpack/issues/1208
- PR #1218: https://github.com/cloudfoundry/php-buildpack/pull/1218
- v4.x Source: `php-buildpack-v4/`
- v5.x Source: `src/php/`
- CF Buildpack Documentation: https://docs.cloudfoundry.org/buildpacks/php/

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-15 | 1.0 | Initial gap analysis |
