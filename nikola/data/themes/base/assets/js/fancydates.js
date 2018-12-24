function fancydates(fanciness, date_format) {
    if (fanciness == 0) {
        return;
    }

    var dates = document.querySelectorAll('.dt-published, .dt-updated, .listdate');

    var l = dates.length;

    for (var i = 0; i < l; i++) {
        var d = moment(dates[i].attributes.datetime.value);
        var o;
        if (fanciness == 1) {
            o = d.local().format(date_format);
        } else {
            o = d.fromNow();
        }
        dates[i].innerHTML = o;
    }
}
