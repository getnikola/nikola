function fancydates(fanciness, luxonDateFormat) {
    if (fanciness === 0) {
        return;
    }

    var dates = document.querySelectorAll('.dt-published, .dt-updated, .listdate');

    var l = dates.length;

    for (var i = 0; i < l; i++) {
        var d = luxon.DateTime.fromISO(dates[i].attributes.datetime.value);
        var o;
        if (fanciness === 1 && luxonDateFormat.preset) {
            o = d.toLocal().toLocaleString(luxon.DateTime[luxonDateFormat.format]);
        } else if (fanciness === 1) {
            o = d.toLocal().toFormat(luxonDateFormat.format);
        } else {
            o = d.toRelative();
        }
        dates[i].innerHTML = o;
    }
}
