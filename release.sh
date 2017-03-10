#!/bin/sh

if [ $# -ne 1 ]; then
    >&2 echo "usage: $0 <version>"
    exit 1
fi

set -o errexit
set -o xtrace

python3 --version
git --version

version=$1

if [[ "$OSTYPE" == "darwin"* ]]; then
	sed -i "" "s/VERSION = .*/VERSION = '${version}'/" */version.py setup.py
else
	sed -i "s/VERSION = .*/VERSION = '${version}'/" */version.py setup.py
fi

tox --skip-missing-interpreters

python3 setup.py sdist bdist_wheel
twine upload dist/*

git checkout */version.py
git checkout setup.py

#git tag -s ${version} -m "${version}"
#git push --tags
