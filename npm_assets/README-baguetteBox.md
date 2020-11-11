BaguetteBox requires patching to make links to image files work.

To patch:

1. `patch node_modules/baguettebox.js/dist/baguetteBox.js baguetteBox-links-with-images-only.patch`
2. Use <https://skalman.github.io/UglifyJS-online/> to create `baguetteBox.min.js` (make sure the license comment is preserved)
