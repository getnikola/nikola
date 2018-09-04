function renderGallery(jsonContent, thumbnailSize) {
    var container = document.getElementById("gallery_container");
    container.innerHTML = '';
    var layoutGeometry = require('justified-layout')(jsonContent, {
    "containerWidth": container.offsetWidth,
    "targetRowHeight": thumbnailSize * 0.6,
    "boxSpacing": 5});
    container.style.height = layoutGeometry.containerHeight + 'px';
    var boxes = layoutGeometry.boxes;
    for (var i = 0; i < boxes.length; i++) {
        var img = document.createElement("img");
        img.setAttribute('src', jsonContent[i].url_thumb);
        img.setAttribute('alt', jsonContent[i].title);
        img.style.width = boxes[i].width + 'px';
        img.style.height = boxes[i].height + 'px';
        link = document.createElement("a");
        link.setAttribute('href', jsonContent[i].url);
        link.setAttribute('class', 'image-reference');
        div = document.createElement("div");
        div.setAttribute('class', 'image-block');
        div.setAttribute('title', jsonContent[i].title);
        div.setAttribute('data-toggle', "tooltip")
        div.style.width = boxes[i].width + 'px';
        div.style.height = boxes[i].height + 'px';
        div.style.top = boxes[i].top + 'px';
        div.style.left = boxes[i].left + 'px';
        link.appendChild(img);
        div.appendChild(link);
        container.appendChild(div);
    }
}

