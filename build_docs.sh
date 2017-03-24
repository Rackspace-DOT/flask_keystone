#!/bin/bash -x

SRC_BRANCH=master
make -C docs clean
make -C docs html
git checkout gh-pages
git checkout $SRC_BRANCH docs
mv -fv docs/build/html/* ./
touch .nojekyll
rm -rf docs
git add -A
git commit -m "Generated gh-pages for `git log $SRC_BRANCH -1 --pretty=short --abbrev-commit`" && git push origin gh-pages ; git checkout $SRC_BRANCH
