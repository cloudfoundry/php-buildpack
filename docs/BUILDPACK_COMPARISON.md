# PHP Buildpack v5.x Architecture Comparison

This document compares the PHP buildpack v5.x architecture with other Cloud Foundry buildpacks to demonstrate alignment with CF buildpack best practices.

## Table of Contents
- [Overview](#overview)
- [Environment Variable Handling](#environment-variable-handling)
- [Configuration Patterns](#configuration-patterns)
- [Service Binding Patterns](#service-binding-patterns)
- [Profile.d Script Usage](#profiled-script-usage)
- [Key Findings](#key-findings)

---

## Overview

The PHP buildpack v5.x has been refactored from Python (v4.x) to Go, aligning it with the architecture patterns used across all other Cloud Foundry buildpacks.

### Buildpacks Analyzed

| Buildpack | Language | VCAP_SERVICES Support | Config Pattern |
|-----------|----------|----------------------|----------------|
| **PHP v5.x** | Go | ✅ Staging-time | Build-time placeholders |
| PHP v4.x | Python | ✅ Staging + Runtime | Runtime rewrite |
| Go | Go | ✅ Staging-time | No placeholders |
| Java | Go | ✅ Staging-time | No placeholders |
| Ruby | Go | ✅ Staging-time | No placeholders |
| Python | Go | ✅ Staging-time | No placeholders |
| .NET Core | Go | ✅ Staging-time | No placeholders |
| Node.js | Go | ✅ Staging-time | No placeholders |

**Key Observation:** All modern CF buildpacks (except PHP v4.x) use **staging-time** configuration with **no runtime rewriting**.

---

## Environment Variable Handling

### Pattern: Read During Staging, Configure at Build Time

All buildpacks follow this pattern:

```
STAGING PHASE:
1. Read environment variables (VCAP_SERVICES, VCAP_APPLICATION, etc.)
2. Parse and extract needed values
3. Write configuration files
4. Create profile.d scripts for runtime env vars

RUNTIME:
- Pre-configured files already in droplet
- profile.d scripts export additional env vars
- No config rewriting needed
```

### PHP v5.x Implementation

**Extension Context (supply phase):**

```go
// src/php/extensions/extension.go
func NewContext() (*Context, error) {
    // Read VCAP_SERVICES during staging
    if vcapServicesJSON := os.Getenv("VCAP_SERVICES"); vcapServicesJSON != "" {
        json.Unmarshal([]byte(vcapServicesJSON), &ctx.VcapServices)
    }
    
    // Read VCAP_APPLICATION during staging
    if vcapAppJSON := os.Getenv("VCAP_APPLICATION"); vcapAppJSON != "" {
        json.Unmarshal([]byte(vcapAppJSON), &ctx.VcapApplication)
    }
    
    return ctx, nil
}
```

### Go Buildpack Implementation

**AppDynamics Hook (supply phase):**

```go
// go-buildpack/src/go/hooks/appdynamics.go
func (h AppdynamicsHook) BeforeCompile(stager *libbuildpack.Stager) error {
    // Read VCAP_SERVICES during staging
    vcapServices := os.Getenv("VCAP_SERVICES")
    services := make(map[string][]Plan)
    json.Unmarshal([]byte(vcapServices), &services)
    
    if val, ok := services["appdynamics"]; ok {
        // Extract credentials
        appdEnv := map[string]string{
            "APPD_CONTROLLER_HOST": val[0].Credentials.ControllerHost,
            "APPD_ACCOUNT_KEY":     val[0].Credentials.AccountAccessKey,
        }
        
        // Write profile.d script
        stager.WriteProfileD("appdynamics.sh", scriptContents)
    }
}
```

### Java Buildpack Implementation

**VCAP Services Helper (supply phase):**

```go
// java-buildpack/src/java/common/context.go
type VCAPServices map[string][]VCAPService

func GetVCAPServices() (VCAPServices, error) {
    vcapServicesStr := os.Getenv("VCAP_SERVICES")
    if vcapServicesStr == "" {
        return VCAPServices{}, nil
    }
    
    var services VCAPServices
    err := json.Unmarshal([]byte(vcapServicesStr), &services)
    return services, err
}
```

Used in frameworks:
```go
// java-buildpack/src/java/frameworks/sealights_agent.go
vcapServices, err := GetVCAPServices()
if sealightsService, found := findService(vcapServices, "sealights"); found {
    // Configure agent with service credentials
}
```

---

## Configuration Patterns

### What All Buildpacks Do

| Pattern | PHP v5.x | Go | Java | Ruby | Python |
|---------|----------|-----|------|------|--------|
| **Read env vars during staging** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Parse VCAP_SERVICES** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Write config files at build time** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Create profile.d scripts** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **No runtime config rewriting** | ✅ | ✅ | ✅ | ✅ | ✅ |

### What NO Buildpack Does (Except PHP v4.x)

| Feature | PHP v4.x | All Others (including PHP v5.x) |
|---------|----------|---------------------------------|
| **Runtime config file rewriting** | ✅ Unique | ❌ Never had |
| **@{ARBITRARY_VAR} placeholders** | ✅ Unique | ❌ Never had |
| **Rewrite on every container start** | ✅ Unique | ❌ Never had |

---

## Service Binding Patterns

### Common Use Case: NewRelic Configuration

All buildpacks configure NewRelic the same way:

#### PHP v5.x

```go
// src/php/extensions/newrelic/newrelic.go
const newrelicEnvScript = `if [[ -z "${NEWRELIC_LICENSE:-}" ]]; then
  export NEWRELIC_LICENSE=$(echo $VCAP_SERVICES | jq -r '.newrelic[0].credentials.licenseKey')
fi`

// Install() writes this script to profile.d during staging
```

#### Go Buildpack

```go
// go-buildpack integrates NewRelic via multi-buildpack
// Same pattern: reads VCAP_SERVICES during staging
```

#### Java Buildpack

```go
// java-buildpack reads VCAP_SERVICES during staging
// Configures NewRelic agent with extracted credentials
```

### Common Use Case: Database Credentials

No buildpack writes database credentials to config files. All use application code:

#### PHP Application Code (Recommended)

```php
<?php
$vcap = json_decode(getenv('VCAP_SERVICES'), true);
$db = $vcap['mysql'][0]['credentials'];

$pdo = new PDO(
    "mysql:host={$db['host']};dbname={$db['name']}",
    $db['username'],
    $db['password']
);
?>
```

#### Ruby Application Code

```ruby
require 'json'

vcap_services = JSON.parse(ENV['VCAP_SERVICES'])
mysql = vcap_services['mysql'].first['credentials']

ActiveRecord::Base.establish_connection(
  adapter: 'mysql2',
  host: mysql['host'],
  username: mysql['username'],
  password: mysql['password'],
  database: mysql['name']
)
```

#### Java Application Code

```java
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

String vcapServices = System.getenv("VCAP_SERVICES");
JsonNode services = new ObjectMapper().readTree(vcapServices);
JsonNode mysql = services.get("mysql").get(0).get("credentials");

String url = "jdbc:mysql://" + mysql.get("host").asText() + "/" + mysql.get("name").asText();
String username = mysql.get("username").asText();
String password = mysql.get("password").asText();
```

**Pattern:** All buildpacks expect applications to parse VCAP_SERVICES in code, not config files.

---

## Profile.d Script Usage

### Standard Pattern Across All Buildpacks

**Purpose:** Set environment variables at runtime based on staging-time analysis.

**Location:** `deps/{idx}/profile.d/*.sh` (sourced by Cloud Foundry at container startup)

### PHP v5.x Examples

#### 1. PHP Environment Setup

```bash
# Written by CreatePHPEnvironmentScript()
#!/usr/bin/env bash
: ${DEPS_DIR:=/home/vcap/deps}
export DEPS_DIR
export PATH="$DEPS_DIR/0/php/bin:$DEPS_DIR/0/php/sbin:$PATH"
```

#### 2. NewRelic Extension

```bash
# Written by NewRelic extension during staging
#!/usr/bin/env bash
if [[ -z "${NEWRELIC_LICENSE:-}" ]]; then
  export NEWRELIC_LICENSE=$(echo $VCAP_SERVICES | jq -r '.newrelic[0].credentials.licenseKey')
fi
```

#### 3. Extension Services (User Extensions)

```bash
# Generated from extension.json preprocess_commands
#!/usr/bin/env bash
# Extension environment variables
export MY_VAR='value'
export ANOTHER_VAR='value2'
```

### Go Buildpack Examples

#### AppDynamics Configuration

```bash
# go-buildpack/src/go/hooks/appdynamics.go generates:
#!/usr/bin/env bash
export APPD_APP_NAME=my-app
export APPD_TIER_NAME=web-tier
export APPD_CONTROLLER_HOST=controller.example.com
export APPD_ACCOUNT_KEY=secret-key
```

### Ruby Buildpack Examples

#### Rails SECRET_KEY_BASE

```bash
# ruby-buildpack generates during staging:
#!/usr/bin/env bash
export SECRET_KEY_BASE=${SECRET_KEY_BASE:-generated-secret-from-rake}
export RAILS_ENV=${RAILS_ENV:-production}
```

### Key Observations

1. **All buildpacks use profile.d** for runtime environment setup
2. **Scripts can parse VCAP_SERVICES** at runtime if needed
3. **Values extracted during staging** can be baked into scripts
4. **No buildpack rewrites config files** at runtime

---

## Key Findings

### 1. PHP v5.x is FULLY Aligned with CF Standards

The refactored PHP buildpack follows the exact same patterns as all other Cloud Foundry buildpacks:

| Capability | Status |
|-----------|--------|
| Read VCAP_SERVICES during staging | ✅ Same as all buildpacks |
| Parse and use service credentials | ✅ Same as all buildpacks |
| Write profile.d scripts | ✅ Same as all buildpacks |
| No runtime config rewriting | ✅ Same as all buildpacks |
| Build-time configuration | ✅ Same as all buildpacks |

### 2. The v4.x Runtime Rewrite Was PHP-Unique

The `bin/rewrite` script and `@{ARBITRARY_VAR}` placeholder support was:

- ❌ **Not used by any other buildpack**
- ❌ **Not a CF buildpack standard**
- ❌ **Had performance/security trade-offs**
- ✅ **Removed for good reasons**

### 3. All Migration Paths Exist

Every v4.x pattern has a v5.x equivalent that matches other buildpacks:

| v4.x Pattern | v5.x Equivalent | Used By |
|--------------|-----------------|---------|
| Extension reads VCAP_SERVICES | Extension reads VCAP_SERVICES | All buildpacks |
| profile.d scripts | profile.d scripts | All buildpacks |
| App code parses VCAP_SERVICES | App code parses VCAP_SERVICES | All buildpacks |
| ~~@{VCAP_SERVICES} in configs~~ | ❌ Never standard | PHP v4.x only |

### 4. No Functionality Lost vs Other Buildpacks

When compared to **other buildpacks** (not v4.x), PHP v5.x has:

- ✅ **Same capabilities**
- ✅ **Same patterns**
- ✅ **Same limitations**
- ✅ **Same extension model**

The only "lost" feature is one that **no other buildpack ever had**.

---

## Conclusion

### PHP Buildpack v5.x Achieves Ecosystem Alignment

The migration from Python (v4.x) to Go (v5.x) successfully:

1. ✅ Aligns with Cloud Foundry buildpack best practices
2. ✅ Follows patterns used by Go, Java, Ruby, Python, .NET buildpacks
3. ✅ Maintains all standard CF functionality
4. ✅ Improves performance (no runtime rewriting)
5. ✅ Enhances security (reduced runtime code execution)
6. ✅ Increases maintainability (Go vs Python)

### The v4.x Runtime Rewrite

While the removal of runtime config rewriting is a breaking change for PHP users:

- It was **never a CF standard** (PHP-only feature)
- It had **performance and security costs**
- All use cases have **standard CF equivalents**
- The change brings **alignment with the broader ecosystem**

### Recommendation

The PHP buildpack v5.x should be considered **fully compliant** with Cloud Foundry buildpack architecture standards and best practices.

---

## See Also

- [VCAP_SERVICES_USAGE.md](./VCAP_SERVICES_USAGE.md) - Detailed VCAP_SERVICES usage guide
- [REWRITE_MIGRATION.md](REWRITE_MIGRATION.md) - v4.x to v5.x migration guide
- [libbuildpack Documentation](https://github.com/cloudfoundry/libbuildpack) - Shared library used by all Go buildpacks
