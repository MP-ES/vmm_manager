#!/bin/bash

set -e

flake8 .
isort --check-only --diff .
