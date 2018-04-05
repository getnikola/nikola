#!/bin/bash

# Update all npm packages
cd npm_assets
npm update
cd ..

# Link bootstrap assets to bootstrap
pushd nikola/data/themes/bootstrap4/assets/js
ln -sf ../../../../../../npm_assets/node_modules/bootstrap/dist/js/bootstrap.min.js .
git add .
popd

pushd nikola/data/themes/bootstrap4/assets/css
ln -sf ../../../../../../npm_assets/node_modules/bootstrap/dist/css/bootstrap.min.css .
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

# Link moment.js and html5shiv to base theme
pushd nikola/data/themes/base/assets/js
ln -sf ../../../../../../npm_assets/node_modules/moment/min/moment-with-locales.min.js .
ln -sf ../../../../../../npm_assets/node_modules/html5shiv/dist/html5shiv-printshiv.min.js .
ln -sf ../../../../../../npm_assets/node_modules/html5shiv/dist/html5shiv-printshiv.min.js html5.js
git add moment-with-locales.min.js html5.js html5shiv-printshiv.min.js
popd

# Link jQuery to bootstrap theme
pushd nikola/data/themes/bootstrap4/assets/js
ln -sf ../../../../../../npm_assets/node_modules/jquery/dist/jquery.min.js .
git add .
popd

# Link Popper.js to bootstrap theme
pushd nikola/data/themes/bootstrap4/assets/js
ln -sf ../../../../../../npm_assets/node_modules/popper.js/dist/umd/popper.min.js .
git add .
popd


pushd nikola/plugins/command/auto
ln -sf ../../../../npm_assets/node_modules/livereload-js/dist/livereload.js .
popd

scripts/generate_symlinked_list.sh

# vim:tw=0
