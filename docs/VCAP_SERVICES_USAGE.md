# VCAP_SERVICES Usage in PHP Buildpack

This document explains how the PHP buildpack handles Cloud Foundry service bindings (VCAP_SERVICES) and compares our approach with other Cloud Foundry buildpacks.

## Table of Contents
- [Quick Summary](#quick-summary)
- [VCAP_SERVICES Availability](#vcap_services-availability)
- [How PHP Buildpack v5.x Uses VCAP_SERVICES](#how-php-buildpack-v5x-uses-vcap_services)
- [Comparison with Other Buildpacks](#comparison-with-other-buildpacks)
- [Migration from v4.x](#migration-from-v4x)
- [Best Practices](#best-practices)

---

## Quick Summary

**TL;DR:**
- ✅ VCAP_SERVICES **IS available** during staging (in Go code)
- ✅ Extensions **CAN read** VCAP_SERVICES to configure agents
- ✅ Can write profile.d scripts with parsed service credentials
- ❌ `@{VCAP_SERVICES}` **NOT available** as config file placeholder
- ✅ PHP v5.x follows same patterns as all other CF buildpacks

---

## VCAP_SERVICES Availability

### When is VCAP_SERVICES Available?

Cloud Foundry provides `VCAP_SERVICES` as an environment variable during **both staging and runtime**:

| Phase | VCAP_SERVICES Available? | How to Access |
|-------|--------------------------|---------------|
| **Staging (Supply/Finalize)** | ✅ Yes | `os.Getenv("VCAP_SERVICES")` in Go code |
| **Runtime (Container Startup)** | ✅ Yes | `getenv('VCAP_SERVICES')` in PHP code or `$VCAP_SERVICES` in shell |

**Important:** VCAP_SERVICES is available during staging, allowing buildpacks to:
- Detect bound services
- Extract credentials
- Configure agents and extensions
- Write configuration files

---

## How PHP Buildpack v5.x Uses VCAP_SERVICES

### 1. Extension Context Initialization

During the supply phase, the extension framework automatically parses VCAP_SERVICES:

**Code Location:** `src/php/extensions/extension.go:77-82`

```go
// Parse VCAP_SERVICES
if vcapServicesJSON := os.Getenv("VCAP_SERVICES"); vcapServicesJSON != "" {
    if err := json.Unmarshal([]byte(vcapServicesJSON), &ctx.VcapServices); err != nil {
        return nil, fmt.Errorf("failed to parse VCAP_SERVICES: %w", err)
    }
}
```

This makes VCAP_SERVICES available to all extensions via `ctx.VcapServices`.

### 2. Extension Usage Examples

#### NewRelic Extension

**Code Location:** `src/php/extensions/newrelic/newrelic.go`

```go
// Writes a profile.d script that extracts license key at runtime
const newrelicEnvScript = `if [[ -z "${NEWRELIC_LICENSE:-}" ]]; then
  export NEWRELIC_LICENSE=$(echo $VCAP_SERVICES | jq -r '.newrelic[0].credentials.licenseKey')
fi`
```

**What it does:**
1. During staging: Creates profile.d script
2. At runtime: Script extracts NewRelic license from VCAP_SERVICES

#### Sessions Extension

**Code Location:** `src/php/extensions/sessions/sessions.go`

```go
func (e *SessionsExtension) loadSession(ctx *extensions.Context) BaseSetup {
    // Search for appropriately named session store in VCAP_SERVICES
    for _, services := range ctx.VcapServices {
        for _, service := range services {
            serviceName := service.Name
            // Check if service matches Redis or Memcached patterns
            if strings.Contains(strings.ToLower(serviceName), "redis") {
                return &RedisSetup{Service: service}
            }
            if strings.Contains(strings.ToLower(serviceName), "memcache") {
                return &MemcachedSetup{Service: service}
            }
        }
    }
    return nil
}
```

**What it does:**
1. During staging: Parses VCAP_SERVICES to find Redis/Memcached services
2. Configures PHP session handler accordingly
3. Writes php.ini with session configuration

#### AppDynamics Extension

**Code Location:** `src/php/extensions/appdynamics/appdynamics.go`

Similar pattern - reads VCAP_SERVICES during staging to configure agent.

---

## Comparison with Other Buildpacks

### All CF Buildpacks Follow the Same Pattern

After analyzing Go, Java, Ruby, and Python buildpacks, we found **all buildpacks use VCAP_SERVICES the same way**:

#### Go Buildpack

**Code Location:** `go-buildpack/src/go/hooks/appdynamics.go:75`

```go
func (h AppdynamicsHook) BeforeCompile(stager *libbuildpack.Stager) error {
    vcapServices := os.Getenv("VCAP_SERVICES")
    services := make(map[string][]Plan)
    err := json.Unmarshal([]byte(vcapServices), &services)
    
    if val, ok := services["appdynamics"]; ok {
        // Configure AppDynamics agent
        // Write profile.d script with environment variables
    }
}
```

#### Java Buildpack

**Code Location:** `java-buildpack/src/java/common/context.go:106`

```go
func GetVCAPServices() (VCAPServices, error) {
    vcapServicesStr := os.Getenv("VCAP_SERVICES")
    if vcapServicesStr == "" {
        return VCAPServices{}, nil
    }
    // Parse and return services
}
```

Used in multiple frameworks (Sealights, JVMKill, etc.)

#### Ruby/Python Buildpacks

Similar patterns - all read VCAP_SERVICES during staging to configure services.

### What NO Buildpack Does

**Config File Placeholders:** No buildpack (except PHP v4.x) ever supported using `@{VCAP_SERVICES}` or other runtime environment variables as **config file placeholders**.

| Feature | PHP v4.x | PHP v5.x | Go | Java | Ruby | Python |
|---------|----------|----------|-----|------|------|--------|
| Read VCAP_SERVICES in code (staging) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Configure from VCAP_SERVICES | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Write profile.d scripts | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **@{VCAP_SERVICES} in config files** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

**Key Insight:** The runtime config rewrite feature (using `@{VCAP_SERVICES}` in config files) was **unique to PHP v4.x** and not a standard Cloud Foundry pattern.

---

## Migration from v4.x

### What Changed

PHP v4.x had **two** mechanisms for using VCAP_SERVICES:

1. **Staging-time (like v5.x):** Extensions read VCAP_SERVICES in Python code
2. **Runtime (removed in v5.x):** `bin/rewrite` script allowed `@{VCAP_SERVICES}` in config files

PHP v5.x removed mechanism #2, aligning with all other Cloud Foundry buildpacks.

### Scenarios That No Longer Work

#### Scenario 1: VCAP_SERVICES in Config Files

**v4.x (NO LONGER WORKS):**
```ini
# .bp-config/php/fpm.d/db.conf
[www]
env[DB_HOST] = @{VCAP_SERVICES}  ; ← Runtime rewrite expanded this
```

**v5.x Migration Option 1 - Application Code:**
```php
<?php
// Parse in application code
$vcap = json_decode(getenv('VCAP_SERVICES'), true);
$db = $vcap['mysql'][0]['credentials'];
$host = $db['host'];
?>
```

**v5.x Migration Option 2 - profile.d Script:**
```bash
#!/bin/bash
# .profile.d/parse-vcap.sh
export DB_HOST=$(echo $VCAP_SERVICES | jq -r '.mysql[0].credentials.host')
export DB_PORT=$(echo $VCAP_SERVICES | jq -r '.mysql[0].credentials.port')
export DB_NAME=$(echo $VCAP_SERVICES | jq -r '.mysql[0].credentials.name')
```

Then in FPM config:
```ini
[www]
env[DB_HOST] = ${DB_HOST}
env[DB_PORT] = ${DB_PORT}
env[DB_NAME] = ${DB_NAME}
```

#### Scenario 2: CF_INSTANCE_* Variables

**v4.x (NO LONGER WORKS):**
```ini
[www]
env[INSTANCE_INDEX] = @{CF_INSTANCE_INDEX}
```

**v5.x Migration - Shell Variables:**
```ini
[www]
env[INSTANCE_INDEX] = ${CF_INSTANCE_INDEX}
```

Or read in application code:
```php
<?php
$instanceIndex = getenv('CF_INSTANCE_INDEX');
?>
```

---

## Best Practices

### ✅ Recommended Patterns

#### 1. Use Built-in Extension Support

For common services, let extensions handle VCAP_SERVICES automatically:

**NewRelic:**
```bash
# Just bind the service
cf bind-service my-app my-newrelic-service
# Extension automatically configures NewRelic
```

**Redis/Memcached Sessions:**
```bash
# Bind Redis service
cf bind-service my-app my-redis
# Extension automatically configures PHP sessions
```

#### 2. Profile.d Scripts for Custom Services

For custom service parsing:

**File:** `.profile.d/parse-services.sh`
```bash
#!/bin/bash

# Extract database credentials
if [[ -n "$VCAP_SERVICES" ]]; then
    export DB_HOST=$(echo $VCAP_SERVICES | jq -r '.mysql[0].credentials.host')
    export DB_PORT=$(echo $VCAP_SERVICES | jq -r '.mysql[0].credentials.port')
    export DB_USER=$(echo $VCAP_SERVICES | jq -r '.mysql[0].credentials.username')
    export DB_PASS=$(echo $VCAP_SERVICES | jq -r '.mysql[0].credentials.password')
    export DB_NAME=$(echo $VCAP_SERVICES | jq -r '.mysql[0].credentials.name')
fi
```

Then use in PHP:
```php
<?php
$host = getenv('DB_HOST');
$port = getenv('DB_PORT');
// ...
?>
```

#### 3. Application Code Parsing

For complex service logic:

```php
<?php
class VcapParser {
    private $services;
    
    public function __construct() {
        $vcapJson = getenv('VCAP_SERVICES');
        $this->services = $vcapJson ? json_decode($vcapJson, true) : [];
    }
    
    public function getService($label, $name = null) {
        if (!isset($this->services[$label])) {
            return null;
        }
        
        $services = $this->services[$label];
        if ($name === null) {
            return $services[0] ?? null;
        }
        
        foreach ($services as $service) {
            if ($service['name'] === $name) {
                return $service;
            }
        }
        return null;
    }
    
    public function getCredentials($label, $name = null) {
        $service = $this->getService($label, $name);
        return $service ? $service['credentials'] : null;
    }
}

// Usage
$vcap = new VcapParser();
$mysqlCreds = $vcap->getCredentials('mysql');
$host = $mysqlCreds['host'];
?>
```

### ❌ Anti-Patterns (Don't Do This)

#### 1. Trying to Use @{VCAP_SERVICES} Placeholders

```ini
# DOES NOT WORK - Not a supported placeholder
[www]
env[SERVICES] = @{VCAP_SERVICES}
```

#### 2. Expecting Runtime Config Changes Without Restaging

```bash
# If you change service bindings:
cf unbind-service my-app old-db
cf bind-service my-app new-db

# Must restage to pick up new VCAP_SERVICES in config:
cf restage my-app  # Required!
cf restart my-app  # Not sufficient if using build-time config
```

**Exception:** If using `${VCAP_SERVICES}` in shell contexts or reading in PHP code, restart is sufficient.

---

## Summary

### PHP Buildpack v5.x is Aligned with CF Standards

The PHP buildpack v5.x follows the same VCAP_SERVICES patterns as all other Cloud Foundry buildpacks:

1. ✅ Read VCAP_SERVICES during staging
2. ✅ Configure extensions and agents
3. ✅ Write profile.d scripts
4. ✅ Parse and extract service credentials
5. ❌ No config file placeholders for arbitrary env vars

### The v4.x Runtime Rewrite Was PHP-Specific

The ability to use `@{VCAP_SERVICES}` in config files was:
- **Unique to PHP v4.x** - No other buildpack had this
- **Removed for good reasons:**
  - Performance (no runtime rewriting)
  - Security (reduced attack surface)
  - Predictability (configs locked at staging)
  - Alignment with other buildpacks

### Migration is Straightforward

All v4.x VCAP_SERVICES use cases have clear v5.x equivalents:
- Extension-based configuration (same as v4.x)
- Profile.d scripts (standard CF pattern)
- Application code parsing (standard practice)

For detailed migration examples, see [REWRITE_MIGRATION.md](REWRITE_MIGRATION.md).

---

## See Also

- [REWRITE_MIGRATION.md](REWRITE_MIGRATION.md) - Complete v4.x to v5.x migration guide
- [Cloud Foundry VCAP_SERVICES Documentation](https://docs.cloudfoundry.org/devguide/deploy-apps/environment-variable.html#VCAP-SERVICES)
- [PHP Extensions Guide](./EXTENSIONS.md) - How to create custom extensions
