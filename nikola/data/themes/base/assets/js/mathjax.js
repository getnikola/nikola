//  We wait for the onload function to load MathJax after the page is completely loaded.  
//  MathJax is loaded 1 unit of time after the page is ready.
//  This hack prevent problems when you use social button from addthis.
//
window.onload = function () {
  setTimeout(function () {
    var script = document.createElement("script");
    script.src  = "https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML";
    document.getElementsByTagName("body")[0].appendChild(script);
  },1)
}
