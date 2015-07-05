#!/bin/bash

# Update all bower packages
bower update

# Link bootstrap3 theme to bootstrap
pushd nikola/data/themes/bootstrap3/assets/js/
ln -sf ../../../../../../bower_components/bootstrap/dist/js/*js .
rm npm.js
git add .
popd

pushd nikola/data/themes/bootstrap3/assets/css/
ln -sf ../../../../../../bower_components/bootstrap/dist/css/* .
git add .
popd

pushd nikola/data/themes/bootstrap3/assets/fonts/
ln -sf ../../../../../../bower_components/bootstrap/dist/fonts/* .
git add .
popd

# Link moment.js to base theme
pushd nikola/data/themes/base/assets/js
ln -sf ../../../../../../bower_components/moment/min/moment-with-locales.min.js .
git add moment-with-locales.min.js
popd

# Link jQuery to bootstrap theme
pushd nikola/data/themes/bootstrap3/assets/js
ln -sf ../../../../../../bower_components/jquery/dist/* .
git add .
popd


# Link colorbox into bootstrap theme
pushd nikola/data/themes/bootstrap3/assets/js
ln -sf ../../../../../../bower_components/jquery-colorbox/jquery.colorbox.js .
git add jquery.colorbox.js
popd

pushd nikola/data/themes/bootstrap3/assets/js/colorbox-i18n
ln -sf ../../../../../../../bower_components/jquery-colorbox/i18n/* .
git add .
popd

pushd nikola/data/themes/bootstrap3/assets/css/
ln -sf ../../../../../../bower_components/jquery-colorbox/example3/colorbox.css .
git add colorbox.css
popd

pushd nikola/data/themes/bootstrap3/assets/css/images/
ln -sf ../../../../../../../bower_components/jquery-colorbox/example3/images/* .
git add .
popd

scripts/generate_symlinked_list.sh
