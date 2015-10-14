/**
 * Flowr.js - Simple jQuery plugin to emulate Flickr's justified view
 * For usage information refer to http://github.com/kalyan02/flowr-js
 *
 *
 * @author: Kalyan Chakravarthy (http://KalyanChakravarthy.net)
 * @version: v0.1
 */
(function($) {
    //$("#container2").css( 'border', '1px solid #ccc');
    $.fn.flowr = function(options) {

        $this = this;
        var ROW_CLASS_NAME = 'flowr-row'; // Class name for the row of flowy
        var MAX_LAST_ROW_GAP = 25; // If the width of last row is lesser than max-width, recalculation is needed
        var NO_COPY_FIELDS = ['complete', 'data', 'responsive']; // these attributes will not be carried forward for append related calls
        var DEFAULTS = {
            'data': [],
            'padding': 5, // whats the padding between flowy items
            'height': 240, // Minimum height an image row should take
            'render': null, // callback function to get the tag
            'append': false, // TODO
            'widthAttr': 'width', // a custom data structure can specify which attribute refers to height/width
            'heightAttr': 'height',
            'maxScale': 1.5, // In case there is only 1 elment in last row
            'maxWidth': this.width() - 1, // 1px is just for offset
            'itemWidth': null, // callback function for width
            'itemHeight': null, // callback function for height
            'complete': null, // complete callback
            'rowClassName': ROW_CLASS_NAME,
            'rows': -1, // Maximum number of rows to render. -1 for no limit.
            'responsive': true // make content responsive
        };
        var settings = $.extend(DEFAULTS, options);

        // If data is being appended, we already have settings
        // If we already have settings, retrieve them
        if (settings.append && $this.data('lastSettings')) {
            lastSettings = $this.data('lastSettings');

            // Copy over the settings from previous init
            for (attr in DEFAULTS) {
                if (NO_COPY_FIELDS.indexOf(attr) < 0 && settings[attr] == DEFAULTS[attr]) {
                    settings[attr] = lastSettings[attr];
                }
            }

            // Check if we have an incomplete last row
            lastRow = $this.data('lastRow');
            if (lastRow.data.length > 0 && settings.maxWidth - lastRow.width > MAX_LAST_ROW_GAP) {
                // Prepend the incomplete row to newly loaded data and redraw
                lastRowData = lastSettings.data.slice(lastSettings.data.length - lastRow.data.length - 1);
                settings.data = lastRowData.concat(settings.data);

                // Remove the incomplete row
                // TODO: Don't reload this stuff later. Reattach to new row.
                $('.' + settings.rowClassName + ':last', $this).detach();
            } else {
                // console.log( lastRow.data.length );
                // console.log( lastRow.width );
            }
        }

        // only on the first initial call
        if (!settings.responsive && !settings.append)
            $this.width($this.width());

        // Basic sanity checks
        if (!(settings.data instanceof Array))
            return;

        if (typeof(settings.padding) != 'number')
            settings.padding = parseInt(settings.padding);

        if (typeof(settings.itemWidth) != 'function') {
            settings.itemWidth = function(data) {
                return data[settings.widthAttr];
            }
        }

        if (typeof(settings.itemHeight) != 'function') {
            settings.itemHeight = function(data) {
                return data[settings.heightAttr];
            }
        }

        // A standalone utility to calculate the item widths for a particular row
        // Returns rowWidth: width occupied & data : the items in the new row
        var utils = {
                getNextRow: function(data, settings) {
                    var itemIndex = 0;
                    var itemsLength = data.length;
                    var lineItems = [];
                    var lineWidth = 0;
                    var maxWidth = settings.maxWidth;
                    var paddingSize = settings.padding;

                    // console.log( 'maxItems=' + data.length );

                    requiredPadding = function() {
                        var extraPads = arguments.length == 1 ? arguments[0] : 0;
                        return (lineItems.length - 1 + extraPads) * settings.padding;
                    }

                    while (lineWidth + requiredPadding() < settings.maxWidth && (itemIndex < itemsLength)) {
                        var itemData = data[itemIndex];
                        var itemWidth = settings.itemWidth.call($this, itemData);
                        var itemHeight = settings.itemHeight.call($this, itemData);

                        var minHeight = settings.height;
                        var minWidth = Math.floor(itemWidth * settings.height / itemHeight);


                        if (minWidth > settings.maxWidth) {
                            // very short+wide images like panoramas
                            // show them even if ugly, as wide as possible
                            minWidth = settings.maxWidth - 1 - requiredPadding(1);
                            minHeight = settings.height * minHeight / minWidth;
                        }
                        var newLineWidth = lineWidth + minWidth;

                        // console.log( 'lineWidth = ' + lineWidth );
                        // console.log( 'newLineWidth = ' + newLineWidth );
                        if (newLineWidth < settings.maxWidth) {
                            lineItems.push({
                                'height': minHeight,
                                'width': minWidth,
                                'itemData': itemData
                            });

                            lineWidth += minWidth;
                            itemIndex++;
                        } else {
                            // We'd have exceeded width. So break off to scale.
                            // console.log( 'breaking off = ' + itemIndex );
                            // console.log( 'leave off size = ' + lineItems.length );
                            break;
                        }
                    } //while

                    // Scale the size to max width
                    testWidth = 0;
                    if (lineWidth < settings.maxWidth) {
                        var fullScaleWidth = settings.maxWidth - requiredPadding() - 10;
                        var currScaleWidth = lineWidth;
                        var scaleFactor = fullScaleWidth / currScaleWidth;
                        if (scaleFactor > settings.maxScale)
                            scaleFactor = 1;

                        var newHeight = Math.round(settings.height * scaleFactor);
                        for (i = 0; i < lineItems.length; i++) {
                            var lineItem = lineItems[i];
                            lineItem.width = Math.floor(lineItem.width * scaleFactor);
                            lineItem.height = newHeight;

                            testWidth += lineItem.width;
                        }
                    }

                    return {
                        data: lineItems,
                        width: testWidth + requiredPadding()
                    };
                }, //getNextRow
                reorderContent: function() {
                    /*
                     TODO: optimize for faster resizing by reusing dom objects instead of killing the dom
                     */
                    var _initialWidth = $this.data('width');
                    var _newWidth = $this.width();
                    var _change = _initialWidth - _newWidth;

                    if (_initialWidth != _newWidth) {
                        $this.html('');
                        var _settings = $this.data('lastSettings');
                        _settings.data = $this.data('data');
                        _settings.maxWidth = $this.width() - 1;
                        $this.flowr(_settings);
                    }
                }
            } //utils

        // If the resposive var is set to true then listen for resize method
        // and prevent resizing from happening twice if responsive is set again during append phase!
        if (settings.responsive && !$this.data('__responsive')) {
            $(window).resize(function() {
                initialWidth = $this.data('width');
                newWidth = $this.width();

                //initiate resize
                if (initialWidth != newWidth) {
                    var task_id = $this.data('task_id');
                    if (task_id) {
                        task_id = clearTimeout(task_id);
                        task_id = null;
                    }
                    task_id = setTimeout(utils.reorderContent, 80);
                    $this.data('task_id', task_id);
                }
            });
            $this.data('__responsive', true);
        }


        return this.each(function() {

            // Get a copy of original data. 1 level deep copy is sufficient.
            var data = settings.data.slice(0);
            var rowData = null;
            var currentRow = 0;
            var currentItem = 0;

            // Store all the data
            var allData = $this.data('data') || [];
            for (i = 0; i < data.length; i++) {
                allData.push(data[i]);
            }
            $this.data('data', allData);

            // While we have a new row
            while ((rowData = utils.getNextRow(data, settings)) != null && rowData.data.length > 0) {
                if (settings.rows > 0 && currentRow >= settings.rows)
                    break;
                // remove the number of elements in the new row from the top of data stack
                data.splice(0, rowData.data.length);

                // Create a new row div, add class, append the htmls and insert the flowy items
                var $row = $('<div>').addClass(settings.rowClassName);
                var slack = $this[0].clientWidth - rowData.width - 2 * settings.padding
                for (i = 0; i < rowData.data.length; i++) {
                    var displayData = rowData.data[i];
                    // Get the HTML object from custom render function passed as argument
                    var displayObject = settings.render.call($this, displayData);
                    displayObject = $(displayObject);
                    extraw = Math.floor(slack/rowData.data.length)
                    if (i == 0) {
                        extraw += slack % rowData.data.length
                    }
                    // Set some basic stuff
                    displayObject
                        .css('width', displayData.width + extraw)
                        .css('height', displayData.height)
                        .css('margin-bottom', settings.padding + "px")
                        .css('margin-left', i == 0 ? '0' : settings.padding + "px"); //TODO:Refactor
                    $row.append(displayObject);

                    currentItem++;
                }
                $this.append($row);
                // console.log ( "I> rowData.data.length="+rowData.data.length +"   rowData.width="+rowData.width );

                currentRow++;
                $this.data('lastRow', rowData);
            }
            // store the current state of settings and the items in last row
            // we'll need this info when we append more items
            $this.data('lastSettings', settings);

            // onComplete callback
            // pass back info about list of rows and items rendered
            if (typeof(settings.complete) == 'function') {
                var completeData = {
                    renderedRows: currentRow,
                    renderedItems: currentItem
                }
                settings.complete.call($this, completeData);
            }
        });
    };

})(jQuery);
