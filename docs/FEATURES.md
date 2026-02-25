# PHP Buildpack Feature Coverage

This document provides comprehensive coverage of all features supported by the PHP buildpack v5.x, with integration test verification and implementation details. **This is for buildpack developers and maintainers.**

> **For end users:** See [USER_GUIDE.md](USER_GUIDE.md) for how to use these features.

## Table of Contents
- [Feature Overview](#feature-overview)
- [Test Coverage Summary](#test-coverage-summary)
- [Detailed Feature Documentation](#detailed-feature-documentation)
- [Implementation Notes](#implementation-notes)

---

## Feature Overview

### Supported Features by Category

| Category | Features | Test Status | User Docs |
|----------|----------|-------------|-----------|
| **Web Servers** | HTTPD, Nginx, FPM-only, Custom pools | ✅ Full | ✅ Complete |
| **PHP Versions** | 8.3.x, 8.2.x, 8.1.x, 8.0.x | ✅ Full | ✅ Complete |
| **Extensions** | 30+ standard + custom | ✅ Full | ✅ Complete |
| **APM** | NewRelic, AppDynamics, Dynatrace | ✅ Full | ✅ Complete |
| **Sessions** | Redis, Memcached | ⚠️ Implicit | ✅ Complete |
| **Frameworks** | CakePHP, Laminas, Symfony, Laravel | ✅ Partial | ✅ Complete |
| **Composer** | Auto-detect, caching, custom paths | ✅ Full | ✅ Complete |
| **Configuration** | php.ini, php.ini.d, fpm.d | ✅ Full | ✅ Complete |
| **Advanced** | Multi-buildpack, extensions | ✅ Full | ✅ Complete |

---

## Test Coverage Summary

### Integration Test Files

```
src/php/integration/
├── web_servers_test.go       # Web server configurations
├── modules_test.go            # PHP extensions and modules
├── composer_test.go           # Composer and dependencies
├── apms_test.go              # APM integrations
├── app_frameworks_test.go    # Framework support
├── default_test.go           # Basic and multi-buildpack
├── python_extension_test.go  # Legacy extensions
└── offline_test.go           # Offline/cached buildpack
```

### Test Fixtures

```
fixtures/
├── with_httpd/              # Apache HTTPD configuration
├── with_nginx/              # Nginx configuration
├── php_with_fpm_d/          # Custom FPM pools
├── php_with_php_ini_d/      # Custom php.ini.d
├── with_amqp/               # AMQP extension
├── with_apcu/               # APCu extension
├── with_phpredis/           # Redis extension
├── with_argon2/             # Argon2 hashing
├── with_compiled_modules/   # User-compiled extensions
├── composer_default/        # Composer workflow
├── cake/                    # CakePHP framework
├── laminas/                 # Laminas framework
├── json_extension/          # JSON user extension
└── dotnet_core_as_supply_app/ # Multi-buildpack
```

---

## Detailed Feature Documentation

### 1. Web Servers

#### Apache HTTPD (Default)

**Test Coverage:** ✅ `web_servers_test.go`
```go
context("PHP app with httpd web server", func() {
    it("builds and runs the app", func() {
        deployment, _, err := platform.Deploy.Execute(name, 
            filepath.Join(fixtures, "with_httpd"))
        Expect(err).NotTo(HaveOccurred())
        Eventually(deployment).Should(Serve(ContainSubstring("PHP Version")))
    })
})
```

**Implementation:**
- Location: `src/php/supply/supply.go` - `InstallHTTPD()`
- Config source: `src/php/config/defaults/config/httpd/`
- User config: `.bp-config/httpd/`
- Placeholders: `@{WEBDIR}`, `@{PHP_FPM_LISTEN}`, `${HOME}`, `${PORT}`

**Configuration Files:**
- `httpd.conf` - Main configuration
- `extra/httpd-modules.conf` - Module loading
- Custom user configs in `.bp-config/httpd/`

---

#### Nginx

**Test Coverage:** ✅ `web_servers_test.go`
```go
context("PHP app with nginx web server", func() {
    it("builds and runs the app", func() {
        deployment, _, err := platform.Deploy.Execute(name, 
            filepath.Join(fixtures, "with_nginx"))
        Expect(err).NotTo(HaveOccurred())
        Eventually(deployment).Should(Serve(ContainSubstring("PHP Version")))
    })
})
```

**Implementation:**
- Location: `src/php/supply/supply.go` - `installNginx()`
- Config source: `src/php/config/defaults/config/nginx/`
- User config: `.bp-config/nginx/`
- Runtime variable substitution via sed in start script
- Placeholders: `@{HOME}`, `@{WEBDIR}`, `@{PHP_FPM_LISTEN}`, `${PORT}`, `${TMPDIR}`

---

#### PHP-FPM Only (No Web Server)

**Test Coverage:** ✅ `web_servers_test.go`
**Implementation:** `WEB_SERVER: "none"` option
**Use Case:** Multi-buildpack scenarios, external web servers

---

#### Custom FPM Pool Configuration

**Test Coverage:** ✅ `web_servers_test.go` - "Default PHP web server with fpm.d dir"
**Fixture:** `fixtures/php_with_fpm_d/`

**Test Verification:**
```go
it("builds and runs the app", func() {
    Eventually(deployment).Should(Serve(SatisfyAll(
        ContainSubstring("TEST_WEBDIR == htdocs"),
        ContainSubstring("TEST_HOME_PATH == /home/vcap/app/test/path"),
    )))
})
```

**Implementation:**
- User configs: `.bp-config/php/fpm.d/*.conf`
- Processed in: `src/php/finalize/finalize.go` - with app context
- Placeholders: `@{HOME}` → `/home/vcap/app`, `@{WEBDIR}`, `@{LIBDIR}`, `@{TMPDIR}`

**Test File:**
```ini
; fixtures/php_with_fpm_d/.bp-config/php/fpm.d/test.conf
[www]
env[TEST_HOME_PATH] = @{HOME}/test/path
env[TEST_WEBDIR] = @{WEBDIR}
```

---

### 2. PHP Extensions

#### Extension Loading

**Test Coverage:** ✅ `modules_test.go`

**All Extensions Test:**
```go
context("app loads all listed extensions", func() {
    it("loads the modules", func() {
        // Tests loading 30+ extensions simultaneously
        ItLoadsAllTheModules(deployment)
    })
})
```

**Implementation:**
- Extension config: `src/php/config/config.go` - `ProcessPhpIni()`
- Placeholder replacement: `@{PHP_EXTENSIONS}`, `@{ZEND_EXTENSIONS}`
- Supply phase processing

---

#### AMQP (RabbitMQ)

**Test Coverage:** ✅ `modules_test.go` - "app with amqp module"
**Fixture:** `fixtures/with_amqp/`

```go
it("amqp module is loaded", func() {
    Eventually(deployment).Should(Serve(ContainSubstring("amqp")))
})
```

**composer.json:**
```json
{
  "require": {
    "ext-amqp": "*"
  }
}
```

---

#### APCu (Caching)

**Test Coverage:** ✅ `modules_test.go` - "app with APCu module"
**Fixture:** `fixtures/with_apcu/`

```go
it("apcu module is loaded", func() {
    Eventually(deployment).Should(Serve(ContainSubstring("apcu")))
})
```

---

#### Redis (phpredis)

**Test Coverage:** ✅ `modules_test.go` - "app with phpredis module"
**Fixture:** `fixtures/with_phpredis/`

```go
it("logs that phpredis could not connect to server", func() {
    // Extension loads, connection test expected to fail without Redis service
    Eventually(logs).Should(ContainSubstring("Connection refused"))
})
```

---

#### Argon2 (Password Hashing)

**Test Coverage:** ✅ `modules_test.go` - "app with argon2 module"
**Fixture:** `fixtures/with_argon2/`

```go
it("argon2 module is loaded", func() {
    Eventually(deployment).Should(Serve(ContainSubstring("argon2")))
})
```

---

#### Compiled Custom Modules

**Test Coverage:** ✅ `modules_test.go` - "app with compiled modules in PHP_EXTENSIONS"
**Fixture:** `fixtures/with_compiled_modules/`

**Implementation:** User-provided `.so` files in `.bp-config/php/lib/`

---

### 3. Composer and Dependencies

#### Default Composer Workflow

**Test Coverage:** ✅ `composer_test.go` - "default PHP composer app"
**Fixture:** `fixtures/composer_default/`

```go
it("loads and installs dependencies", func() {
    Eventually(deployment).Should(Serve(ContainSubstring("Guzzle")))
})
```

**Implementation:**
- Detection: `src/php/extensions/composer/composer.go` - `Detect()`
- Installation: `Install()` method
- Caching: `.bp/composer/` cache directory
- Command: `composer install --no-dev --no-progress --no-interaction`

---

#### Custom Composer Path

**Test Coverage:** ✅ `composer_test.go`
**Fixture:** `fixtures/composer_custom_path/`

**Implementation:** `COMPOSER_PATH` environment variable

---

#### GitHub OAuth Token

**Test Coverage:** ✅ `composer_test.go` - "deployed with invalid COMPOSER_GITHUB_OAUTH_TOKEN"

```go
it("validates token and skips if invalid", func() {
    Eventually(logs).Should(ContainSubstring("Invalid GitHub token"))
})
```

**Implementation:**
- Token validation: `setupGitHubToken()` method
- Rate limit check: GitHub API call
- Graceful fallback if invalid

---

### 4. Application Performance Monitoring

#### NewRelic

**Test Coverage:** ✅ `apms_test.go` - "app with newrelic configured"
**Extension:** `src/php/extensions/newrelic/`

```go
it("loads newrelic", func() {
    Eventually(deployment).Should(Serve(ContainSubstring("newrelic")))
})
```

**Implementation:**
- VCAP_SERVICES detection during supply phase
- Agent download from NewRelic
- License key extraction
- Profile.d script creation: `newrelic-env.sh`

**Profile.d Script:**
```bash
if [[ -z "${NEWRELIC_LICENSE:-}" ]]; then
  export NEWRELIC_LICENSE=$(echo $VCAP_SERVICES | jq -r '.newrelic[0].credentials.licenseKey')
fi
```

---

#### AppDynamics

**Test Coverage:** ✅ `apms_test.go` - "app with appdynamics configured"
**Extension:** `src/php/extensions/appdynamics/`

**Implementation:**
- Service binding detection
- Agent download
- Controller configuration
- Tier/node name configuration

---

#### Dynatrace

**Test Coverage:** ✅ `apms_test.go` - "multiple dynatrace services"

**Implementation:** Service binding detection and agent setup

---

### 5. Session Management

#### Redis Sessions

**Test Coverage:** ⚠️ Implicit (via service binding tests)
**Extension:** `src/php/extensions/sessions/`

**Implementation:**
```go
func (e *SessionsExtension) loadSession(ctx *extensions.Context) BaseSetup {
    for _, services := range ctx.VcapServices {
        for _, service := range services {
            if strings.Contains(strings.ToLower(service.Name), "redis") {
                return &RedisSetup{Service: service}
            }
        }
    }
}
```

**Configuration:**
- Auto-detects Redis service in VCAP_SERVICES
- Writes `session.save_handler = redis`
- Configures `session.save_path` from credentials

---

#### Memcached Sessions

**Test Coverage:** ⚠️ Implicit
**Extension:** `src/php/extensions/sessions/`

**Implementation:** Similar to Redis, detects "memcache" in service name

---

### 6. Application Frameworks

#### CakePHP

**Test Coverage:** ✅ `app_frameworks_test.go` - "CakePHP"
**Fixture:** `fixtures/cake/`

```go
context("CakePHP", func() {
    it("builds and serves the application", func() {
        Eventually(deployment).Should(Serve(ContainSubstring("CakePHP")))
    })
})
```

---

#### Laminas (Zend Framework)

**Test Coverage:** ✅ `app_frameworks_test.go` - "Laminas"
**Fixture:** `fixtures/laminas/`

```go
context("Laminas", func() {
    it("builds and serves the application", func() {
        Eventually(deployment).Should(Serve(ContainSubstring("Laminas")))
    })
})
```

---

#### Symfony / Laravel

**Test Coverage:** ⚠️ Implicit (covered through Composer tests)
**Support:** Via Composer dependency management

---

### 7. Configuration

#### Custom php.ini.d

**Test Coverage:** ✅ `modules_test.go` - "app with custom conf files in php.ini.d dir"
**Fixture:** `fixtures/php_with_php_ini_d/`

```go
it("app sets custom conf and replaces placeholders", func() {
    Eventually(deployment).Should(Serve(SatisfyAll(
        ContainSubstring("teststring"),
        ContainSubstring("/home/vcap/app/lib"),
    )))
})
```

**Implementation:**
- User configs: `.bp-config/php/php.ini.d/*.ini`
- Processed in: `src/php/finalize/finalize.go` - with app context (BUG FIX)
- Placeholders: `@{HOME}` → `/home/vcap/app`

**Test File:**
```ini
; fixtures/php_with_php_ini_d/.bp-config/php/php.ini.d/php.ini
error_prepend_string = 'teststring'
include_path = ".:/usr/share/php:@{HOME}/lib"
```

**Context Bug Fix (This PR):**
- **Before:** php.ini.d processed with deps context (`@{HOME}` = `/home/vcap/deps/{idx}`)
- **After:** php.ini.d processed with app context (`@{HOME}` = `/home/vcap/app`)
- **Change:** `src/php/finalize/finalize.go:272-296`

---

#### Preprocess Commands

**Test Coverage:** ✅ Fixture exists: `fixtures/with_preprocess_cmds/`
**Configuration:** `ADDITIONAL_PREPROCESS_CMDS` in options.json

**Implementation:**
- Commands run before app starts
- Use cases: migrations, cache warming, permissions
- Executed via start script

---

### 8. Advanced Features

#### Multi-Buildpack Support

**Test Coverage:** ✅ `default_test.go` - "dotnet core as supply buildpack"
**Fixture:** `fixtures/dotnet_core_as_supply_app/`

```go
it("works with dotnet core buildpack", func() {
    deployment, _, err := platform.Deploy.
        WithBuildpacks("dotnet_core_buildpack", "php_buildpack").
        Execute(name, filepath.Join(fixtures, "dotnet_core_as_supply_app"))
    Eventually(deployment).Should(Serve(ContainSubstring("PHP Version")))
})
```

**Implementation:**
- DEPS_IDX isolation
- Supply vs finalize buildpack roles
- Profile.d script aggregation

---

#### User Extensions (JSON)

**Test Coverage:** ✅ `default_test.go` - "app with JSON-based user extension"
**Fixture:** `fixtures/json_extension/`

```go
it("loads and runs the extension", func() {
    Eventually(deployment).Should(Serve(ContainSubstring("Extension loaded")))
})
```

**Implementation:**
- Location: `.extensions/<name>/extension.json`
- Loader: `src/php/extensions/user/`
- Features: config files, preprocess commands, dependencies

---

#### User Extensions (Python - Legacy)

**Test Coverage:** ✅ `python_extension_test.go`
**Fixture:** `fixtures/python_extension/`

**Implementation:** Legacy v4.x compatibility

---

## Implementation Notes

### Placeholder Replacement System

**Build-Time Placeholders (`@{VAR}`):**

Replaced during finalize phase in `src/php/finalize/finalize.go`:

```go
// PHP configs (deps context)
phpReplacements := map[string]string{
    "@{HOME}":           "/home/vcap/deps/{idx}",
    "@{DEPS_DIR}":       "/home/vcap/deps",
    "@{LIBDIR}":         "lib",
    "@{PHP_FPM_LISTEN}": "127.0.0.1:9000",
    "@{TMPDIR}":         "${TMPDIR}",
}

// FPM/php.ini.d configs (app context)
appContextReplacements := map[string]string{
    "@{HOME}":   "/home/vcap/app",
    "@{WEBDIR}": "htdocs",
    "@{LIBDIR}": "lib",
    "@{TMPDIR}": "${TMPDIR}",
}
```

**Runtime Variables (`${VAR}`):**

Replaced at container startup:
- Nginx: sed replacement in start script
- Apache: Native environment variable expansion
- Shell: Standard bash expansion

---

### Extension Framework

**Location:** `src/php/extensions/extension.go`

**Context Structure:**
```go
type Context struct {
    BuildDir       string
    CacheDir       string
    DepsDir        string
    DepsIdx        string
    VcapServices   map[string][]Service
    VcapApplication VcapApplication
    Env            map[string]string
}
```

**Extension Interface:**
```go
type Extension interface {
    Detect(ctx *Context) (bool, error)
    Install(installer Installer) error
}
```

**Built-in Extensions:**
- `composer/` - Dependency management
- `newrelic/` - NewRelic APM
- `appdynamics/` - AppDynamics APM
- `sessions/` - Session handler configuration
- `user/` - User extension loader

---

### Start Scripts

**Location:** `src/php/finalize/finalize.go`

**Generated Scripts:**
- `start-httpd.sh` - Apache HTTPD + PHP-FPM
- `start-nginx.sh` - Nginx + PHP-FPM  
- `start-fpm.sh` - PHP-FPM only

**Features:**
- Sed variable replacement (PORT, TMPDIR)
- Process management
- Graceful shutdown handling
- Log output

---

## Feature Support Matrix

| Feature | Implementation | Tests | User Docs | Status |
|---------|---------------|-------|-----------|--------|
| **Web Servers** |
| Apache HTTPD | ✅ supply.go | ✅ Tested | ✅ Documented | Complete |
| Nginx | ✅ supply.go | ✅ Tested | ✅ Documented | Complete |
| PHP-FPM Only | ✅ supply.go | ✅ Tested | ✅ Documented | Complete |
| Custom FPM Pools | ✅ finalize.go | ✅ Tested | ✅ Documented | Complete |
| **PHP** |
| Version Selection | ✅ supply.go | ✅ Tested | ✅ Documented | Complete |
| php.ini Override | ✅ supply.go | ⚠️ Implicit | ✅ Documented | Needs test |
| php.ini.d | ✅ finalize.go | ✅ Tested | ✅ Documented | Complete |
| **Extensions** |
| Composer detection | ✅ composer/ | ✅ Tested | ✅ Documented | Complete |
| AMQP | ✅ manifest | ✅ Tested | ✅ Documented | Complete |
| APCu | ✅ manifest | ✅ Tested | ✅ Documented | Complete |
| Redis | ✅ manifest | ✅ Tested | ✅ Documented | Complete |
| Argon2 | ✅ manifest | ✅ Tested | ✅ Documented | Complete |
| All Standard | ✅ manifest | ✅ Tested | ✅ Documented | Complete |
| Custom Compiled | ✅ supply.go | ✅ Tested | ✅ Documented | Complete |
| **APM** |
| NewRelic | ✅ newrelic/ | ✅ Tested | ✅ Documented | Complete |
| AppDynamics | ✅ appdynamics/ | ✅ Tested | ✅ Documented | Complete |
| Dynatrace | ✅ dynatrace/ | ✅ Tested | ✅ Documented | Complete |
| **Sessions** |
| Redis | ✅ sessions/ | ⚠️ Implicit | ✅ Documented | Needs test |
| Memcached | ✅ sessions/ | ⚠️ Implicit | ✅ Documented | Needs test |
| **Frameworks** |
| CakePHP | ✅ Composer | ✅ Tested | ✅ Documented | Complete |
| Laminas | ✅ Composer | ✅ Tested | ✅ Documented | Complete |
| Symfony | ✅ Composer | ⚠️ Implicit | ✅ Documented | Needs test |
| Laravel | ✅ Composer | ⚠️ Implicit | ✅ Documented | Needs test |
| **Advanced** |
| Multi-buildpack | ✅ supply.go | ✅ Tested | ✅ Documented | Complete |
| User Extensions | ✅ user/ | ✅ Tested | ✅ Documented | Complete |
| Preprocess Cmds | ✅ finalize.go | ✅ Fixture | ✅ Documented | Needs test |
| Standalone Apps | ✅ finalize.go | ⚠️ Implicit | ✅ Documented | Needs test |

**Legend:**
- ✅ Complete - Implemented, tested, documented
- ⚠️ Implicit - Works but lacks explicit integration test
- ❌ Missing - Not implemented

---

## Test Gaps to Address

### Features Needing Explicit Tests

1. **Custom php.ini** - Fixture exists but no explicit test
2. **Redis Sessions** - Works but needs service binding test
3. **Memcached Sessions** - Works but needs service binding test
4. **Symfony Framework** - Implicit through Composer
5. **Laravel Framework** - Implicit through Composer
6. **Preprocess Commands** - Fixture exists, needs test assertion
7. **Standalone Apps** - APP_START_CMD needs integration test

### Recommended Test Additions

```go
// Redis session test
context("app with redis session store", func() {
    it("configures sessions to use redis", func() {
        // Bind Redis service, verify session handler
    })
})

// Custom php.ini test
context("app with custom php.ini", func() {
    it("applies custom php settings", func() {
        // Verify memory_limit, upload_max_filesize, etc.
    })
})
```

---

## See Also

- [USER_GUIDE.md](USER_GUIDE.md) - End-user documentation
- [VCAP_SERVICES_USAGE.md](VCAP_SERVICES_USAGE.md) - Service binding patterns
- [BUILDPACK_COMPARISON.md](BUILDPACK_COMPARISON.md) - Cross-buildpack comparison
- [REWRITE_MIGRATION.md](REWRITE_MIGRATION.md) - v4.x to v5.x migration

