# PHP Buildpack Rewrite System Migration Guide

## Overview

This document explains the differences between the v4.x runtime rewrite system and the v5.x build-time placeholder replacement system, and provides guidance for users migrating from v4.x to v5.x.

---

## Architecture Comparison

### v4.x (Python-based) - Runtime Rewrite

**Location:** `bin/rewrite` (Python script)

**When executed:** At **runtime** (container startup), before starting PHP-FPM, Apache, or Nginx

**How it works:**
1. During build phase (`bin/compile`), the `bin/rewrite` script is copied to `$HOME/.bp/bin/rewrite`
2. At runtime, extensions register "preprocess commands" that call the rewrite script:
   - PHP: `$HOME/.bp/bin/rewrite "$HOME/php/etc"`
   - Apache: `$HOME/.bp/bin/rewrite "$HOME/httpd/conf"`
   - Nginx: `$HOME/.bp/bin/rewrite "$HOME/nginx/conf"`
3. These commands run **before** the web server or PHP-FPM starts
4. The script has access to **all runtime environment variables** via `ctx.update(os.environ)`

**Implementation:**
```python
# bin/rewrite (v4.x)
ctx = utils.FormattedDict({
    'BUILD_DIR': '',
    'LD_LIBRARY_PATH': '',
    'PATH': '',
    'PYTHONPATH': ''
})
ctx.update(os.environ)  # <-- ALL environment variables available!
utils.rewrite_cfgs(toPath, ctx, delim='@')
```

**Template engine:** Python's `string.Template` with `safe_substitute()`
- Supports `$VAR` and `${VAR}` syntax with configurable delimiter
- Uses `@` as delimiter: `@{VAR}` or `@VAR`
- **`safe_substitute()`**: Leaves unknown variables **unchanged** (doesn't error)

---

### v5.x (Go-based) - Build-Time Replacement

**Location:** `src/php/finalize/finalize.go` (function `ReplaceConfigPlaceholders`)

**When executed:** At **build time** (during finalize phase)

**How it works:**
1. During finalize phase, all config files are processed **once** at build time
2. Placeholders are replaced with **known values** from predefined maps
3. Configs are written to disk with values baked in
4. At runtime, only `PORT` and `TMPDIR` are replaced using `sed` in profile scripts

**Implementation:**
```go
// finalize.go (v5.x)
func ReplaceConfigPlaceholders(...) {
    replacements := map[string]string{
        "@{HOME}":      buildDir,
        "@{PORT}":      "${PORT}",  // Replaced at runtime via sed
        "@{TMPDIR}":    "${TMPDIR}",
        "@{WEBDIR}":    webDir,
        // ... predefined list only
    }
    // Replace each placeholder with its value
}
```

**Template engine:** Simple `strings.Replace()` with predefined map
- Only `@{VAR}` syntax supported
- **No arbitrary environment variables** - only predefined placeholders
- Fails silently if placeholder not in map (leaves unchanged)

---

## Key Differences

| Feature | v4.x (Runtime Rewrite) | v5.x (Build-Time Replacement) |
|---------|------------------------|-------------------------------|
| **Execution Phase** | Runtime (container startup) | Build time (finalize phase) |
| **Environment Access** | **ALL** runtime environment variables via `os.environ` | **Only predefined** variables in replacement maps |
| **Custom Variables** | ✅ Supported - any `VCAP_*`, `CF_*`, custom env vars | ❌ Not supported - only predefined placeholders |
| **Syntax** | `@{VAR}`, `@VAR` (Python Template) | `@{VAR}` only |
| **Unknown Variables** | Left unchanged (`safe_substitute`) | Left unchanged (no match in map) |
| **Runtime Flexibility** | ✅ Can use environment set at staging OR runtime | ❌ Only environment available at build time |
| **Performance** | Slower - rewrites all configs on every start | Faster - configs pre-processed at build |
| **Language** | Python | Go |
| **Script Location** | `$HOME/.bp/bin/rewrite` | Built into finalize binary |

---

## Critical Behavioral Changes in v5.x

### **IMPORTANT: Config File Placeholders vs. Go Code Access**

**Key Distinction:** There's a difference between:
1. **Reading env vars in Go code** (✅ works in v5.x)
2. **Using env vars as `@{...}` config placeholders** (❌ limited in v5.x)

**What This Means:**
- ✅ Extensions CAN read `VCAP_SERVICES` in Go code during staging
- ✅ Applications CAN read `VCAP_SERVICES` in PHP code at runtime
- ❌ Config files CANNOT use `@{VCAP_SERVICES}` as a placeholder
- ❌ Only predefined placeholders like `@{HOME}`, `@{WEBDIR}` work in configs

For detailed buildpack comparison showing PHP v5.x alignment with all other CF buildpacks, see [docs/BUILDPACK_COMPARISON.md](docs/BUILDPACK_COMPARISON.md).

---

### **Build-Time vs Runtime Config Rewriting**

The biggest behavioral change from v4.x to v5.x is **when** configuration rewriting happens:

| Aspect | v4.x (Python) | v5.x (Go) |
|--------|---------------|-----------|
| **When** | Runtime (container startup) | Build time (finalize phase) |
| **Environment** | ALL runtime env vars via `os.environ` | Only staging-time env vars |
| **VCAP_SERVICES** | ✅ Available | ❌ Not available |
| **CF_INSTANCE_*** | ✅ Available | ❌ Not available |
| **Custom runtime vars** | ✅ Available | ❌ Not available (unless set at staging) |
| **Reconfiguration** | ✅ Can change without restage | ❌ Requires restaging |

**What this means:**
- In v4.x, the `bin/rewrite` script ran **before** each app start with access to **all** environment variables
- In v5.x, placeholder replacement runs **during staging** with access to **only** build-time variables
- Runtime-only variables like `VCAP_SERVICES`, `CF_INSTANCE_INDEX`, etc. are **not available** for `@{...}` placeholders

---

## Breaking Changes in v5.x

### 1. **No Arbitrary Environment Variables**

**v4.x behavior:**
```ini
# php.ini
; Works in v4.x - MY_CUSTOM_VAR available at runtime
extension_dir = @{MY_CUSTOM_VAR}/modules
memory_limit = @{MY_MEMORY_LIMIT}
```

**v5.x behavior:**
```ini
# php.ini
; DOES NOT WORK in v5.x - not in predefined map
extension_dir = @{MY_CUSTOM_VAR}/modules  ; ← Left as literal string!

; Only predefined variables work
extension_dir = @{HOME}/.bp-config/php/modules  ; ← Works
```

### 2. **Arbitrary Environment Variables Not Available as @{...} Placeholders**

**IMPORTANT CLARIFICATION:** Environment variables like `VCAP_SERVICES` and `CF_INSTANCE_*` **ARE available during staging** in Go code (for extensions), but **cannot be used as `@{...}` placeholders** in config files.

#### The Distinction:

**✅ WORKS - Reading in Go Code (Staging Time):**
```go
// Extensions can read VCAP_SERVICES during staging
vcapServices := os.Getenv("VCAP_SERVICES")
services := parseJSON(vcapServices)
// Use to configure agents, write profile.d scripts, etc.
```

**❌ DOES NOT WORK - Config File Placeholders:**
```ini
# v4.x - WORKED (runtime rewrite expanded @{...})
[www]
env[DB_HOST] = @{VCAP_SERVICES}

# v5.x - DOES NOT WORK (@{VCAP_SERVICES} not in replacement map)
[www]
env[DB_HOST] = @{VCAP_SERVICES}  ; ← Will be left as literal string!
```

#### Variables NOT Supported as @{...} Placeholders:

**Cloud Foundry Service Bindings:**
- `@{VCAP_SERVICES}` - Not a predefined placeholder
- `@{VCAP_APPLICATION}` - Not a predefined placeholder

**Instance-Specific Variables:**
- `@{CF_INSTANCE_INDEX}` - Not a predefined placeholder
- `@{CF_INSTANCE_IP}` - Not a predefined placeholder
- `@{CF_INSTANCE_ADDR}` - Not a predefined placeholder

**Custom Runtime-Only Variables:**
```ini
# v4.x - WORKED (any env var set at runtime)
env[MY_RUNTIME_VAR] = @{MY_RUNTIME_VAR}

# v5.x - DOES NOT WORK (unless MY_RUNTIME_VAR set during staging)
env[MY_RUNTIME_VAR] = @{MY_RUNTIME_VAR}  ; ← Left unchanged!
```

#### Workarounds:

**Option 1: Use Shell Variables `${VAR}`**
```ini
# FPM pool config - shell variables work
[www]
env[VCAP_SERVICES] = ${VCAP_SERVICES}
env[CF_INSTANCE_INDEX] = ${CF_INSTANCE_INDEX}
```
**Note:** Only works in contexts where shell expansion happens (fpm.d env vars).

**Option 2: Read in Application Code**
```php
<?php
// Parse VCAP_SERVICES in your app
$vcap = json_decode(getenv('VCAP_SERVICES'), true);
$db = $vcap['mysql'][0]['credentials'];
$host = $db['host'];
?>
```

**Option 3: Use .profile.d Scripts**
```bash
#!/bin/bash
# .profile.d/parse-services.sh
# Extract values from VCAP_SERVICES and set env vars
export DB_HOST=$(echo $VCAP_SERVICES | jq -r '.mysql[0].credentials.host')
export DB_PORT=$(echo $VCAP_SERVICES | jq -r '.mysql[0].credentials.port')
```

**Option 4: Set Variables at Staging (manifest.yml)**
```yaml
# Variables set in manifest.yml are available during staging
applications:
- name: my-app
  env:
    MY_VAR: some_value  # Available for @{MY_VAR} during staging
```

### 3. **Supported Placeholders (v5.x)**

Only these placeholders are supported in v5.x. **IMPORTANT:** The meaning of `@{HOME}` varies by config file location (see Context Table below).

#### General Placeholders
- `@{HOME}` - Home directory (context-dependent: app or deps directory)
- `@{TMPDIR}` - Temporary directory (converted to `${TMPDIR}` for runtime expansion)
- `@{LIBDIR}` - Library directory (default: `lib`)
- `@{WEBDIR}` - Web root directory (default: `htdocs`)

#### PHP-Specific Placeholders
- `@{PHP_FPM_LISTEN}` - PHP-FPM listen address (TCP or Unix socket)
- `@{PHP_EXTENSIONS}` - Enabled PHP extensions (replaced during supply phase)
- `@{ZEND_EXTENSIONS}` - Enabled Zend extensions (replaced during supply phase)
- `@{PHP_FPM_CONF_INCLUDE}` - FPM pool config include directive (replaced during supply phase)
- `@{DEPS_DIR}` - Dependencies directory (always `/home/vcap/deps`)

#### Runtime Variables (NOT placeholders)
- `${PORT}` - Application port (shell variable, expanded by sed at runtime)
- `${TMPDIR}` - Temporary directory (shell variable, expanded by sed/shell at runtime)
- `${HOME}` - Application home (shell variable, expanded by Apache/shell at runtime)

**Note:** `@{PORT}` is NOT supported - use `${PORT}` instead for runtime expansion.

#### Context-Aware Placeholder Replacement

The `@{HOME}` placeholder resolves to **different values** depending on where it's used:

| Config Location | `@{HOME}` Value | When Replaced | Purpose |
|----------------|-----------------|---------------|---------|
| `php/etc/php.ini` | `/home/vcap/deps/{idx}` | Finalize | PHP needs deps-relative extension paths |
| `php/etc/php-fpm.conf` | `/home/vcap/deps/{idx}` | Finalize | FPM binary and PID file in deps dir |
| `php/etc/php.ini.d/*.ini` | `/home/vcap/app` | Finalize | User configs reference app paths (include_path, etc.) |
| `php/etc/fpm.d/*.conf` | `/home/vcap/app` | Finalize | Environment vars for PHP scripts (app context) |
| `nginx/conf/*.conf` | `/home/vcap/app` | Finalize | Web server serves app directory |
| `httpd/conf/*.conf` | NOT REPLACED | N/A | Use `${HOME}` for runtime expansion by Apache |

**User-Provided Config Examples:**

**✅ WORKS:** `.bp-config/php/fpm.d/custom.conf`
```ini
[www]
env[MY_PATH] = @{HOME}/storage  ; → /home/vcap/app/storage
env[WEBDIR] = @{WEBDIR}         ; → htdocs
```

**✅ WORKS:** `.bp-config/php/php.ini.d/custom.ini`
```ini
include_path = "@{HOME}/lib:@{HOME}/vendor"  ; → /home/vcap/app/lib:/home/vcap/app/vendor
```

**✅ WORKS:** `.bp-config/nginx/custom.conf`
```nginx
root @{HOME}/@{WEBDIR};                      ; → /home/vcap/app/htdocs
```

**✅ WORKS:** `.bp-config/httpd/extra/custom.conf`
```apache
DocumentRoot "${HOME}/@{WEBDIR}"             ; → ${HOME}/htdocs (Apache expands ${HOME} at runtime)
```

See `finalize.go:258-336` for implementation details.

---

## User-Provided Configuration Files

Users can override buildpack defaults by placing config files in `.bp-config/`:

### Supported User Config Locations

| Location | Copied To | Placeholder Context | When Processed |
|----------|-----------|---------------------|----------------|
| `.bp-config/php/php.ini` | `deps/{idx}/php/etc/` | Deps context | Supply + Finalize |
| `.bp-config/php/php-fpm.conf` | `deps/{idx}/php/etc/` | Deps context | Supply + Finalize |
| `.bp-config/php/fpm.d/*.conf` | `deps/{idx}/php/etc/fpm.d/` | **App context** | Finalize |
| `.bp-config/php/php.ini.d/*.ini` | `deps/{idx}/php/etc/php.ini.d/` | **App context** | Finalize |
| `.bp-config/httpd/**/*` | `BUILD_DIR/httpd/conf/` | App context | Finalize |
| `.bp-config/nginx/**/*` | `BUILD_DIR/nginx/conf/` | App context | Finalize |

### User Config Placeholder Examples

**PHP FPM Pool Config** (`.bp-config/php/fpm.d/env.conf`):
```ini
[www]
; Set environment variables for PHP scripts
env[APP_STORAGE] = @{HOME}/storage          ; Becomes: /home/vcap/app/storage
env[APP_CACHE] = @{TMPDIR}/cache            ; Becomes: ${TMPDIR}/cache
env[WEB_ROOT] = @{HOME}/@{WEBDIR}           ; Becomes: /home/vcap/app/htdocs
```

**PHP Extension Config** (`.bp-config/php/php.ini.d/paths.ini`):
```ini
; Custom include paths for your application
include_path = ".:/usr/share/php:@{HOME}/lib:@{HOME}/vendor"
; Becomes: .:/usr/share/php:/home/vcap/app/lib:/home/vcap/app/vendor

; Restrict file access to app directory
open_basedir = @{HOME}:@{TMPDIR}:/tmp
; Becomes: /home/vcap/app:${TMPDIR}:/tmp
```

**Nginx Config** (`.bp-config/nginx/custom-location.conf`):
```nginx
location /uploads {
    root @{HOME}/@{WEBDIR};                 ; Becomes: /home/vcap/app/htdocs
    client_max_body_size 100M;
}

location ~ \.php$ {
    fastcgi_pass unix:@{PHP_FPM_LISTEN};    ; Becomes: unix:/home/vcap/deps/0/php/var/run/php-fpm.sock
}
```

**Apache HTTPD Config** (`.bp-config/httpd/extra/custom.conf`):
```apache
# Use ${VAR} for runtime expansion by Apache
<Directory "${HOME}/@{WEBDIR}">             # Becomes: ${HOME}/htdocs
    Options Indexes FollowSymLinks
    AllowOverride All
</Directory>

# Use @{VAR} for build-time replacement
ProxyPass /api fcgi://@{PHP_FPM_LISTEN}/${HOME}/@{WEBDIR}
# Becomes: ProxyPass /api fcgi://127.0.0.1:9000/${HOME}/htdocs
```

### Important Notes for User Configs

1. **Context Matters:** `@{HOME}` in `fpm.d/` and `php.ini.d/` means `/home/vcap/app`, not `/home/vcap/deps/{idx}`
2. **No Custom Variables:** Only predefined placeholders work. Cannot use `@{MY_VAR}` - use `${MY_VAR}` instead
3. **Runtime Variables:** Use `${PORT}`, `${TMPDIR}`, `${HOME}` for values that change at runtime
4. **Apache Special:** Apache configs can use `${...}` syntax which Apache expands at runtime

---

## Scenarios That No Longer Work in v5.x

### Scenario 1: Service Credentials in Config Files

**v4.x Pattern (NO LONGER WORKS):**
```ini
# .bp-config/php/fpm.d/db.conf
[www]
; Extract DB hostname from VCAP_SERVICES
env[DB_HOST] = @{VCAP_SERVICES}
```

**v5.x Migration:**
```php
// Parse in application code instead
<?php
$vcap = json_decode(getenv('VCAP_SERVICES'), true);
$db = $vcap['mysql'][0]['credentials'];
// Use $db['host'], $db['port'], etc. in your app
?>
```

Or use `.profile.d` to set env vars:
```bash
#!/bin/bash
# .profile.d/db-env.sh
export DB_HOST=$(echo $VCAP_SERVICES | jq -r '.mysql[0].credentials.host')
export DB_NAME=$(echo $VCAP_SERVICES | jq -r '.mysql[0].credentials.name')
```

---

### Scenario 2: Instance-Specific Configuration

**v4.x Pattern (NO LONGER WORKS):**
```ini
# .bp-config/php/fpm.d/instance.conf
[www]
; Configure based on instance index (for sharding, etc.)
env[INSTANCE_INDEX] = @{CF_INSTANCE_INDEX}
env[INSTANCE_IP] = @{CF_INSTANCE_IP}
```

**v5.x Migration:**
```ini
# Use shell variables instead
[www]
env[INSTANCE_INDEX] = ${CF_INSTANCE_INDEX}
env[INSTANCE_IP] = ${CF_INSTANCE_IP}
```

Or read in PHP:
```php
<?php
$instanceIndex = getenv('CF_INSTANCE_INDEX');
$instanceIP = getenv('CF_INSTANCE_IP');
?>
```

---

### Scenario 3: Dynamic Runtime Reconfiguration

**v4.x Behavior (NO LONGER WORKS):**
```bash
# Could change env vars and restart app
$ cf set-env my-app MY_CONFIG_VAR new_value
$ cf restart my-app
# Config files rewritten with new value on startup ✓
```

**v5.x Behavior:**
```bash
# Environment variables used in @{...} placeholders require restaging
$ cf set-env my-app MY_CONFIG_VAR new_value
$ cf restage my-app  # Must restage, not just restart!
```

**Exception:** Shell variables `${VAR}` still work with just restart:
```bash
$ cf set-env my-app MY_VAR new_value
$ cf restart my-app  # ${MY_VAR} will pick up new value
```

---

### Scenario 4: Complex Environment Variable Expressions

**v4.x Pattern (NO LONGER WORKS):**
```ini
# Could use Python's string.Template with complex expressions
env[CACHE_DIR] = @{TMPDIR}/cache/@{CF_INSTANCE_INDEX}
```

**v5.x Migration:**
```bash
# Use .profile.d script for complex logic
#!/bin/bash
# .profile.d/setup-cache.sh
export CACHE_DIR="${TMPDIR}/cache/${CF_INSTANCE_INDEX}"
mkdir -p "$CACHE_DIR"
```

Then reference in FPM config:
```ini
[www]
env[CACHE_DIR] = ${CACHE_DIR}
```

---

## Migration Strategies

### Strategy 1: Use Runtime Variables (`${VAR}`)

For variables that need runtime values, use shell variable syntax `${VAR}` instead of `@{VAR}`:

**Before (v4.x):**
```ini
; php.ini
memory_limit = @{MY_MEMORY_LIMIT}
```

**After (v5.x):**
```ini
; php.ini  
memory_limit = ${MY_MEMORY_LIMIT}
```

**Requirements:**
- Config file must be processed by a shell (Apache `.htaccess` with `mod_env`, bash scripts)
- OR config format must support environment variable expansion natively

### Strategy 2: Use .profile.d Scripts

For complex runtime logic, use `.profile.d` scripts to rewrite configs at runtime:

```bash
# .profile.d/custom_config.sh
#!/bin/bash

# Manually replace placeholders using sed
sed -i "s|PLACEHOLDER|${MY_VAR}|g" "$HOME/php/etc/php.ini"
```

### Strategy 3: Use Buildpack Extensions

Create a custom extension during supply/finalize phase to add your own placeholder mappings (requires modifying buildpack source).

### Strategy 4: Environment Variable Workarounds

Set environment variables during **staging** (not just runtime) if they need to be used in `@{...}` placeholders:

```yaml
# manifest.yml
applications:
- name: my-app
  env:
    MY_VAR: some_value  # Available during staging
```

---

## Common Use Cases

### Case 1: Database Connection from VCAP_SERVICES

**v4.x:**
```php
<?php
// Could use @{VCAP_SERVICES} in configs at runtime
$vcap = json_decode(getenv('VCAP_SERVICES'), true);
```

**v5.x:**
Use PHP code or runtime scripts, **not** `@{...}` placeholders:
```php
<?php
// Read VCAP_SERVICES at runtime in application code
$vcap = json_decode(getenv('VCAP_SERVICES'), true);
```

### Case 2: Custom PHP Settings Based on Environment

**v4.x:**
```ini
; php.ini
memory_limit = @{PHP_MEMORY_LIMIT}
```

**v5.x Option A - Use default + .user.ini:**
```ini
; .user.ini (per-directory override)
memory_limit = ${PHP_MEMORY_LIMIT}
```

**v5.x Option B - Use .profile.d script:**
```bash
#!/bin/bash
# .profile.d/php_config.sh
echo "memory_limit = ${PHP_MEMORY_LIMIT}" > "$HOME/php/etc/conf.d/99-custom.ini"
```

### Case 3: Dynamic Nginx Configuration

**v4.x:**
```nginx
# nginx.conf
worker_processes @{NGINX_WORKERS};
```

**v5.x:**
```nginx
# nginx.conf - Use predefined placeholder
worker_processes @{NGINX_WORKERS};  # If added to finalize.go replacement map

# OR use environment variable
worker_processes ${NGINX_WORKERS};  # If nginx config loader supports env vars
```

---

## Advantages of v5.x Build-Time Approach

Despite losing runtime flexibility, v5.x offers benefits:

1. **Performance**: No config rewriting on every container start
2. **Simplicity**: No Python dependency at runtime
3. **Security**: Reduced attack surface (no runtime code execution)
4. **Predictability**: Configs are "locked in" at build time
5. **Debugging**: Configs can be inspected in droplet without runtime dependencies

---

## Extending v5.x (For Buildpack Maintainers)

To add support for custom placeholders, modify `src/php/finalize/finalize.go`:

```go
// Add to replacement map in ReplaceConfigPlaceholders()
replacements := map[string]string{
    "@{HOME}":           buildDir,
    "@{MY_CUSTOM_VAR}":  os.Getenv("MY_CUSTOM_VAR"),  // Add this
    // ...
}
```

**Note:** This requires rebuilding the buildpack.

---

## Troubleshooting

### Placeholder Not Being Replaced

**Symptom:** Config file contains literal `@{MY_VAR}` after deployment

**Cause:** Variable not in predefined replacement map

**Solution:** 
1. Check if placeholder is in supported list (see `README.md`)
2. Use `${VAR}` syntax instead if runtime expansion is acceptable
3. Use `.profile.d` script for custom runtime replacements

### Config Works in v4.x but Not v5.x

**Symptom:** Application crashes with config errors after migrating to v5.x

**Cause:** Relying on runtime environment variables in `@{...}` placeholders

**Solution:**
1. Identify which placeholders are failing (check config files for unreplaced `@{...}`)
2. Migrate to `${...}` syntax for runtime variables
3. Or set variables at **staging time** via `manifest.yml` env section

---

## References

- v4.x rewrite implementation: `bin/rewrite` (Python)
- v4.x rewrite logic: `lib/build_pack_utils/utils.py:89` (`rewrite_cfgs()`)
- v5.x replacement logic: `src/php/finalize/finalize.go:240-330`
- Supported placeholders: `README.md:137-192`
- Python Template docs: https://docs.python.org/2/library/string.html#template-strings

---

## Summary

| What You Need | v4.x | v5.x |
|---------------|------|------|
| Predefined buildpack variables | `@{HOME}`, `@{WEBDIR}`, etc. | ✅ Same |
| Custom staging-time env vars | ✅ `@{MY_VAR}` | ❌ Not supported |
| Runtime env vars | ✅ `@{VCAP_SERVICES}` | ❌ Use `${...}` or code |
| Shell variables | `${PORT}`, `${HOME}` | ✅ Same |
| Performance | Slower (runtime rewrite) | ✅ Faster (build-time) |

**Migration Checklist:**
- [ ] Audit all config files for `@{...}` placeholders
- [ ] Identify custom environment variables being used
- [ ] Replace with `${...}` syntax or `.profile.d` scripts
- [ ] Test application on v5.x with runtime environment variables
- [ ] Update documentation for your team

---

## v4.x → v5.x Feature Parity Status

This section documents all features from v4.x and their status in v5.x.

### ✅ Fully Implemented in v5.x

| Feature | v4.x | v5.x | Notes |
|---------|------|------|-------|
| Web Servers | httpd, nginx, none | ✅ httpd, nginx, none | Same options supported |
| PHP-FPM | ✅ | ✅ | Same functionality |
| Composer | ✅ | ✅ | Version detection, ext-* dependencies |
| NewRelic APM | ✅ | ✅ | Via VCAP_SERVICES or env var |
| AppDynamics APM | ✅ | ✅ | Via VCAP_SERVICES |
| Dynatrace | ✅ | ✅ | Via libbuildpack hook |
| Sessions (Redis/Memcached) | ✅ | ✅ | Auto-configured from VCAP_SERVICES |
| WEBDIR auto-setup | ✅ | ✅ | Moves files into htdocs if not exists |
| User config (.bp-config/) | ✅ | ✅ | options.json, httpd/, nginx/, php/ |
| php.ini.d support | ✅ | ✅ | Custom PHP ini files |
| fpm.d support | ✅ | ✅ | Custom FPM pool configs |
| Composer GitHub OAuth | ✅ | ✅ | Via COMPOSER_GITHUB_OAUTH_TOKEN |
| **ADDITIONAL_PREPROCESS_CMDS** | ✅ | ✅ **NEW** | Startup commands in options.json |
| **Standalone PHP Mode** | ✅ | ✅ **NEW** | APP_START_CMD for CLI/workers |
| **User Extensions** | ✅ | ✅ **NEW** | .extensions/ with JSON config |

### 🆕 Newly Implemented Features (v5.x)

#### 1. ADDITIONAL_PREPROCESS_CMDS

Run custom commands at container startup before PHP-FPM starts.

**Configuration (.bp-config/options.json):**
```json
{
  "ADDITIONAL_PREPROCESS_CMDS": [
    "echo 'Starting application'",
    ["./bin/migrations.sh", "--force"],
    "php artisan cache:clear"
  ]
}
```

Commands can be:
- A string: `"echo hello"` - runs as single command
- An array: `["script.sh", "arg1", "arg2"]` - arguments joined with spaces

#### 2. Standalone PHP Mode (APP_START_CMD)

For CLI/worker applications that don't need a web server or PHP-FPM.

**Configuration (.bp-config/options.json):**
```json
{
  "WEB_SERVER": "none",
  "APP_START_CMD": "worker.php"
}
```

**Auto-detection:** If `WEB_SERVER=none` and no `APP_START_CMD` is set, the buildpack searches for:
- `app.php`
- `main.php`
- `run.php`
- `start.php`

If none found, defaults to `app.php`.

#### 3. User Extensions (.extensions/)

Create custom extensions without modifying the buildpack source.

**Create `.extensions/<name>/extension.json`:**
```json
{
  "name": "my-custom-extension",
  "preprocess_commands": [
    "echo 'Extension starting'",
    ["./setup.sh", "arg1"]
  ],
  "service_commands": {
    "worker": "php worker.php --daemon"
  },
  "service_environment": {
    "MY_VAR": "value",
    "ANOTHER_VAR": "value2"
  }
}
```

**Available hooks:**
- `preprocess_commands`: Commands run at startup before PHP-FPM
- `service_commands`: Long-running background services
- `service_environment`: Environment variables for services

**Note:** Unlike v4.x Python extensions, v5.x uses a declarative JSON format for security and simplicity. Dynamic code execution is not supported.

### ❌ Not Implemented (Low Priority)

These v4.x features are not currently in v5.x due to low usage or being deprecated:

| Feature | v4.x | v5.x | Alternative |
|---------|------|------|-------------|
| COMPOSER_INSTALL_GLOBAL | ✅ | ❌ | Add to composer.json require-dev |
| igbinary auto-add for redis | ✅ | ❌ | Explicitly add igbinary to PHP_EXTENSIONS |
| SNMP MIBDIRS auto-set | ✅ | ❌ | Set MIBDIRS in manifest.yml env |
| HHVM support (PHP_VM=hhvm) | ✅ | ❌ | HHVM is deprecated, use PHP |
| Verbose PHP version warnings | ✅ | ❌ | Staging fails with clear error |

### 📋 Migration Notes for Specific Features

#### Migrating Python User Extensions to JSON

**v4.x (.extensions/myext/extension.py):**
```python
def preprocess_commands(ctx):
    return [['echo', 'hello'], ['./setup.sh']]

def service_commands(ctx):
    return {'worker': ('php', 'worker.php', '--daemon')}

def service_environment(ctx):
    return {'MY_VAR': 'value'}
```

**v5.x (.extensions/myext/extension.json):**
```json
{
  "name": "myext",
  "preprocess_commands": [
    ["echo", "hello"],
    ["./setup.sh"]
  ],
  "service_commands": {
    "worker": "php worker.php --daemon"
  },
  "service_environment": {
    "MY_VAR": "value"
  }
}
```

#### Migrating Standalone Apps

**v4.x:**
- Set `WEB_SERVER=none` in options.json
- Buildpack auto-detected entry points
- Or set `APP_START_CMD` in options.json

**v5.x:**
- Same behavior preserved
- Set `WEB_SERVER=none` in options.json
- Optional: Set `APP_START_CMD` explicitly
- Auto-detects: app.php, main.php, run.php, start.php

---

## Complete Migration Checklist

**Before Migration:**
- [ ] Review this document completely
- [ ] Identify any `.extensions/` Python extensions in your app
- [ ] Identify any `ADDITIONAL_PREPROCESS_CMDS` usage
- [ ] Identify if using `WEB_SERVER=none` mode

**During Migration:**
- [ ] Convert Python extensions to JSON format
- [ ] Verify `ADDITIONAL_PREPROCESS_CMDS` still works
- [ ] Test standalone mode if applicable
- [ ] Audit `@{...}` placeholders in config files
- [ ] Replace custom `@{MY_VAR}` with `${MY_VAR}` or `.profile.d` scripts

**After Migration:**
- [ ] Test application thoroughly
- [ ] Verify all startup commands execute
- [ ] Check logs for extension loading messages
- [ ] Validate PHP extensions are enabled correctly
