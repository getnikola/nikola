#!/bin/bash

# Update all bower packages
bower update

# Link bootstrap3 theme to bootstrap
pushd nikola/data/themes/bootstrap3/assets/js/
ln -sf ../../../../../../bower_components/bootstrap/dist/js/*.min.js .
rm npm.js
git add .
popd

pushd nikola/data/themes/bootstrap3/assets/css/
ln -sf ../../../../../../bower_components/bootstrap/dist/css/*.min.css .
git add .
popd

pushd nikola/data/themes/bootstrap3/assets/fonts/
ln -sf ../../../../../../bower_components/bootstrap/dist/fonts/* .
git add .
popd

# Link baguettebox.js to base theme
pushd nikola/data/themes/base/assets/js
ln -sf ../../../../../../bower_components/baguettebox.js/dist/*.min.js .
git add .
popd
pushd nikola/data/themes/base/assets/css
ln -sf ../../../../../../bower_components/baguettebox.js/dist/*.min.css .
git add .
popd

# Link moment.js to base theme
pushd nikola/data/themes/base/assets/js
ln -sf ../../../../../../bower_components/moment/min/moment-with-locales.min.js .
git add moment-with-locales.min.js
popd

# Link jQuery to bootstrap theme
pushd nikola/data/themes/bootstrap3/assets/js
ln -sf ../../../../../../bower_components/jquery/dist/*min* .
git add .
popd


# Link colorbox into bootstrap theme
pushd nikola/data/themes/bootstrap3/assets/js
ln -sf ../../../../../../bower_components/jquery-colorbox/jquery.colorbox-min.js .
git add jquery.colorbox-min.js
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
