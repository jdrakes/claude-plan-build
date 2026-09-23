#!/usr/bin/env bash
set -e

python3 scripts/test_no_leaks.py --self-test
python3 scripts/test_no_leaks.py
