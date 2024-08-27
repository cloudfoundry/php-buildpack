#!/bin/bash
#
#  Run all of the tests.
#
#  Normally, you could just run `nosetests tests/`, but there are some
#   odd conflicts when doing this.  The easiest fix is to just run tests
#   individually.
#
set -e
for TEST in ./tests/*.py; do
    echo "Running test [$TEST]..."
    USE_SYSTEM_PYTHON=1 nosetests --verbose --detailed-errors --nocapture "$@" "$TEST"
    echo
done
