# PHP Buildpack Documentation

This directory contains architectural documentation for the PHP buildpack v5.x.

## Documentation Index

### Features & User Guides

- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user guide for all buildpack features
  - Getting started guide
  - Web server configuration (Apache HTTPD, Nginx, FPM-only)
  - PHP configuration and extensions
  - Composer and dependency management
  - APM integration (NewRelic, AppDynamics, Dynatrace)
  - Session storage (Redis, Memcached)
  - Framework guides (Laravel, CakePHP, Laminas, Symfony)
  - Advanced features and troubleshooting

- **[FEATURES.md](FEATURES.md)** - Developer reference with test coverage verification
  - Feature list with test references
  - Integration test locations (file:line)
  - Fixture paths and examples
  - Implementation details
  - Test coverage analysis
  - Test gaps and notes

### Architecture & Design

- **[BUILDPACK_COMPARISON.md](BUILDPACK_COMPARISON.md)** - Comparison with other CF buildpacks (Go, Java, Ruby, Python)
  - Environment variable handling patterns
  - Configuration approaches
  - Service binding patterns
  - Profile.d script usage
  - Demonstrates PHP v5.x alignment with CF standards

### Service Bindings

- **[VCAP_SERVICES_USAGE.md](VCAP_SERVICES_USAGE.md)** - Comprehensive guide to VCAP_SERVICES
  - When VCAP_SERVICES is available (staging vs runtime)
  - How extensions use VCAP_SERVICES
  - Comparison with other buildpacks
  - Migration strategies from v4.x
  - Best practices and anti-patterns

### Migration Guides

- **[V4_V5_MIGRATION_GAP_ANALYSIS.md](V4_V5_MIGRATION_GAP_ANALYSIS.md)** - Comprehensive v4.x to v5.x feature comparison
  - Complete feature matrix (what's implemented, missing, or changed)
  - Missing features: `ADDITIONAL_PREPROCESS_CMDS`, `APP_START_CMD`, User Extensions
  - Implementation roadmap and priorities
  - Testing recommendations

- **[REWRITE_MIGRATION.md](REWRITE_MIGRATION.md)** - v4.x to v5.x migration guide
  - Rewrite system changes
  - Breaking changes
  - Migration strategies
  - User-provided config handling

## Quick Links

### For Users

**New to the buildpack?**
1. Start with [USER_GUIDE.md](USER_GUIDE.md) to see what's supported
2. Check examples for your web server (HTTPD, Nginx, etc.)
3. Review [Best Practices](#best-practices) below

**Migrating from v4.x?**
1. **Start here:** [V4_V5_MIGRATION_GAP_ANALYSIS.md](V4_V5_MIGRATION_GAP_ANALYSIS.md) for complete feature comparison
2. Read [REWRITE_MIGRATION.md](REWRITE_MIGRATION.md) for breaking changes
3. Check [VCAP_SERVICES_USAGE.md](VCAP_SERVICES_USAGE.md) for service binding patterns
4. Review feature parity in [USER_GUIDE.md](USER_GUIDE.md)

**Using VCAP_SERVICES?**
- See [VCAP_SERVICES_USAGE.md](VCAP_SERVICES_USAGE.md) for complete guide
- Extensions automatically handle common services (NewRelic, Redis sessions)
- Use profile.d scripts or application code for custom services

### For Developers

**Understanding the Architecture?**
1. Read [BUILDPACK_COMPARISON.md](BUILDPACK_COMPARISON.md) to see how PHP v5.x aligns with other buildpacks
2. Review [libbuildpack](https://github.com/cloudfoundry/libbuildpack) for shared library patterns
3. Check source code organization in [../src/php/](../src/php/)

**Creating Extensions?**
- Extension framework in [../src/php/extensions/](../src/php/extensions/)
- Context provides parsed VCAP_SERVICES and VCAP_APPLICATION
- Write profile.d scripts for runtime environment setup

## Best Practices

### ✅ Recommended Patterns

#### 1. Use Built-in Extensions
```bash
# NewRelic - just bind the service
cf bind-service my-app my-newrelic

# Redis Sessions - just bind the service
cf bind-service my-app my-redis
```

#### 2. Profile.d for Service Parsing
```bash
# .profile.d/parse-vcap.sh
export DB_HOST=$(echo $VCAP_SERVICES | jq -r '.mysql[0].credentials.host')
```

#### 3. Application Code for Database Credentials
```php
<?php
$vcap = json_decode(getenv('VCAP_SERVICES'), true);
$db = $vcap['mysql'][0]['credentials'];
$pdo = new PDO("mysql:host={$db['host']};dbname={$db['name']}", ...);
?>
```

### ❌ Anti-Patterns

#### 1. Trying to Use @{VCAP_SERVICES} Placeholders
```ini
# DOES NOT WORK - Not a supported placeholder
[www]
env[DB] = @{VCAP_SERVICES}
```

#### 2. Expecting Config Changes Without Restaging
```bash
cf bind-service my-app new-db
cf restart my-app  # NOT SUFFICIENT if configs use build-time placeholders
cf restage my-app  # REQUIRED to pick up new service binding
```

## Key Concepts

### Build-Time vs Runtime

**Build-Time (Staging):**
- Placeholder replacement happens once
- Config files written with known values
- Extensions run and configure services
- Profile.d scripts created

**Runtime:**
- Configs already processed
- Profile.d scripts sourced
- No config rewriting
- Better performance and security

### Placeholder Types

**Build-Time Placeholders (`@{VAR}`):**
- Replaced during finalize phase
- Only predefined variables: `@{HOME}`, `@{WEBDIR}`, `@{LIBDIR}`, etc.
- See [REWRITE_MIGRATION.md](REWRITE_MIGRATION.md) for complete list

**Runtime Variables (`${VAR}`):**
- Standard shell/environment variables
- `${PORT}`, `${TMPDIR}`, `${VCAP_SERVICES}`, etc.
- Expanded by shell or application code

### Extension Context

Extensions have access to:
- `ctx.VcapServices` - Parsed VCAP_SERVICES
- `ctx.VcapApplication` - Parsed VCAP_APPLICATION  
- `ctx.BuildDir`, `ctx.DepsDir` - Directory paths
- `ctx.Env` - All environment variables

Example:
```go
func (e *MyExtension) Install(installer extensions.Installer) error {
    // Access parsed VCAP_SERVICES
    for _, services := range e.ctx.VcapServices {
        for _, service := range services {
            // Configure based on service credentials
        }
    }
}
```

## Alignment with Cloud Foundry Standards

PHP buildpack v5.x follows the **same patterns as all other CF buildpacks**:

| Pattern | PHP v5.x | Go | Java | Ruby | Python |
|---------|----------|-----|------|------|--------|
| Read VCAP_SERVICES in code (staging) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Configure from service bindings | ✅ | ✅ | ✅ | ✅ | ✅ |
| Write profile.d scripts | ✅ | ✅ | ✅ | ✅ | ✅ |
| No runtime config rewriting | ✅ | ✅ | ✅ | ✅ | ✅ |
| @{VCAP_SERVICES} placeholders | ❌ | ❌ | ❌ | ❌ | ❌ |

**Key Insight:** The v4.x runtime rewrite was PHP-specific. Removing it brings alignment with CF ecosystem standards.

## Additional Resources

### Cloud Foundry Documentation
- [VCAP_SERVICES](https://docs.cloudfoundry.org/devguide/deploy-apps/environment-variable.html#VCAP-SERVICES)
- [Buildpacks](https://docs.cloudfoundry.org/buildpacks/)
- [Application Environment Variables](https://docs.cloudfoundry.org/devguide/deploy-apps/environment-variable.html)

### Related Buildpacks
- [libbuildpack](https://github.com/cloudfoundry/libbuildpack) - Shared Go library
- [Go Buildpack](https://github.com/cloudfoundry/go-buildpack)
- [Java Buildpack](https://github.com/cloudfoundry/java-buildpack)
- [Ruby Buildpack](https://github.com/cloudfoundry/ruby-buildpack)
- [Python Buildpack](https://github.com/cloudfoundry/python-buildpack)

---

## Contributing to Documentation

When adding new documentation:

1. **User-facing docs** → Update this README with links
2. **Migration guides** → Add to [REWRITE_MIGRATION.md](REWRITE_MIGRATION.md)
3. **Architecture docs** → Create new file in this directory
4. **Code examples** → Include in relevant guide

**Style Guidelines:**
- Use clear section headers
- Include code examples
- Show both ✅ working and ❌ non-working patterns
- Link to related documentation
- Keep language simple and direct
