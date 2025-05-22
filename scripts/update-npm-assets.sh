#!/bin/bash

# Update all npm packages
cd npm_assets
npm update
cd ..

# Link bootstrap assets to bootstrap4
pushd nikola/data/themes/bootstrap4/assets/js
ln -sf ../../../../../../npm_assets/node_modules/bootstrap/dist/js/bootstrap.min.js .
git add .
popd

pushd nikola/data/themes/bootstrap4/assets/css
ln -sf ../../../../../../npm_assets/node_modules/bootstrap/dist/css/bootstrap.min.css .
git add .
popd

# Link bootstrap5 assets to bootstrap5 theme
pushd nikola/data/themes/bootstrap5/assets/js
mkdir -p .
ln -sf ../../../../../../npm_assets/node_modules/bootstrap5/dist/js/bootstrap.min.js .
git add .
popd

pushd nikola/data/themes/bootstrap5/assets/css
mkdir -p .
ln -sf ../../../../../../npm_assets/node_modules/bootstrap5/dist/css/bootstrap.min.css .
git add .
popd

# Link bootstrap5 assets to bootblog5 theme
pushd nikola/data/themes/bootblog5/assets/js
mkdir -p .
ln -sf ../../../../../../npm_assets/node_modules/bootstrap5/dist/js/bootstrap.min.js .
git add .
popd

pushd nikola/data/themes/bootblog5/assets/css
mkdir -p .
ln -sf ../../../../../../npm_assets/node_modules/bootstrap5/dist/css/bootstrap.min.css .
git add .
popd

# Link baguettebox.js to base theme
pushd nikola/data/themes/base/assets/js
ln -sf ../../../../../../npm_assets/node_modules/baguettebox.js/dist/baguetteBox.min.js .
git add .
popd
pushd nikola/data/themes/base/assets/css
ln -sf ../../../../../../npm_assets/node_modules/baguettebox.js/dist/baguetteBox.min.css .
git add .
popd

# Link luxon and html5shiv to base theme
pushd nikola/data/themes/base/assets/js
ln -sf ../../../../../../npm_assets/node_modules/luxon/build/global/luxon.min.js .
ln -sf ../../../../../../npm_assets/node_modules/html5shiv/dist/html5shiv-printshiv.min.js .
ln -sf ../../../../../../npm_assets/node_modules/html5shiv/dist/html5shiv-printshiv.min.js html5.js
git add luxon.min.js html5.js html5shiv-printshiv.min.js
popd

# Link newer luxon to bootstrap5 and bootblog5 themes
pushd nikola/data/themes/bootstrap5/assets/js
mkdir -p .
ln -sf ../../../../../../npm_assets/node_modules/luxon36/build/global/luxon.min.js .
git add .
popd

pushd nikola/data/themes/bootblog5/assets/js
mkdir -p .
ln -sf ../../../../../../npm_assets/node_modules/luxon36/build/global/luxon.min.js .
git add .
popd

# Link jQuery to bootstrap themes
pushd nikola/data/themes/bootstrap4/assets/js
ln -sf ../../../../../../npm_assets/node_modules/jquery/dist/jquery.min.js .
git add .
popd

# Link Popper.js to bootstrap themes
pushd nikola/data/themes/bootstrap4/assets/js
ln -sf ../../../../../../npm_assets/node_modules/popper.js/dist/umd/popper.min.js .
git add .
popd

# Link Popper.js Core to bootstrap5 themes
pushd nikola/data/themes/bootstrap5/assets/js
ln -sf ../../../../../../npm_assets/node_modules/@popperjs/core/dist/umd/popper.min.js .
git add .
popd
#
# pushd nikola/data/themes/bootblog5/assets/js
ln -sf ../../../../../../npm_assets/node_modules/@popperjs/core/dist/umd/popper.min.js .
git add .



pushd nikola/plugins/command/auto
ln -sf ../../../../npm_assets/node_modules/livereload-js/dist/livereload.js .
popd

scripts/generate_symlinked_list.sh

# Verify baguetteBox patch
grep PATCHED npm_assets/node_modules/baguettebox.js/dist/baguetteBox.js > /dev/null || printf '%b' '\033[1;31mWARNING: baguetteBox must be manually patched (in both unminified and minified versions), see npm_assets/baguetteBox-links-with-images-only.patch\033[0m\n'

# vim:tw=0
