# PHP Extension Configuration

This directory contains the YAML files that define which PHP extensions and
native modules are compiled into each PHP binary. These files are passed to
[binary-builder](https://github.com/cloudfoundry/binary-builder) via the
`--extensions-dir` flag during CI builds.

## File Structure

### Base file

`php{major}-base-extensions.yml` defines the full list of extensions for all
minor versions of a PHP major release. Currently:

- `php8-base-extensions.yml` — all extensions for PHP 8.x

### Patch files

`php{major}{minor}-extensions-patch.yml` defines per-minor-version overrides:

- **Exclusions** — extensions in the base file that are incompatible with this
  minor version (removed before compilation).
- **Additions** — replacement versions or new extensions added for this minor
  version.

When an exclusion has a matching addition (same `name`), the addition replaces
the excluded entry in-place, preserving build order.

Currently:
- `php81-extensions-patch.yml`
- `php82-extensions-patch.yml`
- `php83-extensions-patch.yml`
- `php84-extensions-patch.yml`
- `php85-extensions-patch.yml`

## Adding a new PHP minor version

1. Create `php{major}{minor}-extensions-patch.yml` (e.g. `php86-extensions-patch.yml`).
2. Add `exclusions` for any base extensions that are incompatible.
3. Add `additions` with compatible replacement versions.
4. An empty patch is valid (no overrides needed for this minor version):
   ```yaml
   ---
   extensions:
   ```

## Adding a new PHP major version

1. Create `php{major}-base-extensions.yml` (e.g. `php9-base-extensions.yml`).
2. Create patch files for each minor version as needed.

## Entry format

Each extension entry has four fields:

```yaml
- name: redis          # Extension name (matches PECL package name)
  version: 6.0.2       # Version to compile
  md5: def456abc...     # MD5 checksum of the source tarball
  klass: PeclRecipe     # Build recipe class in binary-builder
```

Common `klass` values:
- `PeclRecipe` — standard PECL extension (most common)
- `FakePeclRecipe` — built-in PHP extension compiled from PHP source
- `LuaRecipe`, `HiredisRecipe`, `LibRdKafkaRecipe`, etc. — native module recipes
- `IonCubeRecipe` — IonCube loader (binary download, not compiled)

## Updating extension versions

Use the helper scripts in
[buildpacks-ci/scripts/php-modules/](https://github.com/cloudfoundry/buildpacks-ci/tree/master/scripts/php-modules):

```bash
# Check which extensions are outdated (dry-run, no file changes):
BINARY_BUILDER_DIR=/path/to/binary-builder \
  bundle exec ruby bump-versions.rb --dry-run

# Bump all extensions to latest versions:
./scripts/php-modules/bump-versions.sh

# Recompute MD5 hashes for bumped extensions:
./scripts/php-modules/update-hashes.sh
```

> **Note:** Not all PECL version bumps are compatible with all PHP versions.
> Review the diff carefully after running `bump-versions.sh` — some bumps may
> need to be reverted or moved to per-version patch files.
