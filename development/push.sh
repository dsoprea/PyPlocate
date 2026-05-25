#!/bin/bash -ex

cd "$(dirname "$0")/.."

python3 -m twine upload dist/*
