function fancydates(fanciness, date_format) {
    if (fanciness == 0) {
        return;
    }

    dates = document.getElementsByClassName('dt-published');

    i = 0;
    l = dates.length;

    for (i = 0; i < l; i++) {
        d = moment(dates[i].attributes.datetime.value);
        if (fanciness == 1) {
            o = d.local().format(date_format);
        } else {
            o = d.fromNow();
        }
        dates[i].innerHTML = o;
    }
}
