#!/bin/bash

# Update all npm packages
cd npm_assets
npm update
cd ..

# Link bootstrap3 theme to bootstrap
pushd nikola/data/themes/bootstrap3/assets/js/
ln -sf ../../../../../../npm_assets/node_modules/bootstrap/dist/js/*.min.js* .
git add .
popd

pushd nikola/data/themes/bootstrap3/assets/css/
ln -sf ../../../../../../npm_assets/node_modules/bootstrap/dist/css/*.min.css* .
git add .
popd

pushd nikola/data/themes/bootstrap3/assets/fonts/
ln -sf ../../../../../../npm_assets/node_modules/bootstrap/dist/fonts/* .
git add .
popd

# Link baguettebox.js to base theme
pushd nikola/data/themes/base/assets/js
ln -sf ../../../../../../npm_assets/node_modules/baguettebox.js/dist/*.min.js .
git add .
popd
pushd nikola/data/themes/base/assets/css
ln -sf ../../../../../../npm_assets/node_modules/baguettebox.js/dist/*.min.css .
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
pushd nikola/data/themes/bootstrap3/assets/js
ln -sf ../../../../../../npm_assets/node_modules/jquery/dist/*min* .
git add .
popd

pushd nikola/plugins/command/auto
ln -sf ../../../../npm_assets/node_modules/livereload-js/dist/livereload.js .
popd

scripts/generate_symlinked_list.sh
