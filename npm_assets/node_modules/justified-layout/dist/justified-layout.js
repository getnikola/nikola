require=(function(){function r(e,n,t){function o(i,f){if(!n[i]){if(!e[i]){var c="function"==typeof require&&require;if(!f&&c)return c(i,!0);if(u)return u(i,!0);var a=new Error("Cannot find module '"+i+"'");throw a.code="MODULE_NOT_FOUND",a}var p=n[i]={exports:{}};e[i][0].call(p.exports,function(r){var n=e[i][1][r];return o(n||r)},p,p.exports,r,e,n,t)}return n[i].exports}for(var u="function"==typeof require&&require,i=0;i<t.length;i++)o(t[i]);return o}return r})()({1:[function(require,module,exports){
/*!
 * Copyright 2019 SmugMug, Inc.
 * Licensed under the terms of the MIT license. Please see LICENSE file in the project root for terms.
 * @license
 */

var merge = require('merge');

/**
 * Row
 * Wrapper for each row in a justified layout.
 * Stores relevant values and provides methods for calculating layout of individual rows.
 *
 * @param {Object} layoutConfig - The same as that passed
 * @param {Object} Initialization parameters. The following are all required:
 * @param params.top {Number} Top of row, relative to container
 * @param params.left {Number} Left side of row relative to container (equal to container left padding)
 * @param params.width {Number} Width of row, not including container padding
 * @param params.spacing {Number} Horizontal spacing between items
 * @param params.targetRowHeight {Number} Layout algorithm will aim for this row height
 * @param params.targetRowHeightTolerance {Number} Row heights may vary +/- (`targetRowHeight` x `targetRowHeightTolerance`)
 * @param params.edgeCaseMinRowHeight {Number} Absolute minimum row height for edge cases that cannot be resolved within tolerance.
 * @param params.edgeCaseMaxRowHeight {Number} Absolute maximum row height for edge cases that cannot be resolved within tolerance.
 * @param params.isBreakoutRow {Boolean} Is this row in particular one of those breakout rows? Always false if it's not that kind of photo list
 * @param params.widowLayoutStyle {String} If widows are visible, how should they be laid out?
 * @constructor
 */

var Row = module.exports = function (params) {

	// Top of row, relative to container
	this.top = params.top;

	// Left side of row relative to container (equal to container left padding)
	this.left = params.left;

	// Width of row, not including container padding
	this.width = params.width;

	// Horizontal spacing between items
	this.spacing = params.spacing;

	// Row height calculation values
	this.targetRowHeight = params.targetRowHeight;
	this.targetRowHeightTolerance = params.targetRowHeightTolerance;
	this.minAspectRatio = this.width / params.targetRowHeight * (1 - params.targetRowHeightTolerance);
	this.maxAspectRatio = this.width / params.targetRowHeight * (1 + params.targetRowHeightTolerance);

	// Edge case row height minimum/maximum
	this.edgeCaseMinRowHeight = params.edgeCaseMinRowHeight;
	this.edgeCaseMaxRowHeight = params.edgeCaseMaxRowHeight;

	// Widow layout direction
	this.widowLayoutStyle = params.widowLayoutStyle;

	// Full width breakout rows
	this.isBreakoutRow = params.isBreakoutRow;

	// Store layout data for each item in row
	this.items = [];

	// Height remains at 0 until it's been calculated
	this.height = 0;

};

Row.prototype = {

	/**
	 * Attempt to add a single item to the row.
	 * This is the heart of the justified algorithm.
	 * This method is direction-agnostic; it deals only with sizes, not positions.
	 *
	 * If the item fits in the row, without pushing row height beyond min/max tolerance,
	 * the item is added and the method returns true.
	 *
	 * If the item leaves row height too high, there may be room to scale it down and add another item.
	 * In this case, the item is added and the method returns true, but the row is incomplete.
	 *
	 * If the item leaves row height too short, there are too many items to fit within tolerance.
	 * The method will either accept or reject the new item, favoring the resulting row height closest to within tolerance.
	 * If the item is rejected, left/right padding will be required to fit the row height within tolerance;
	 * if the item is accepted, top/bottom cropping will be required to fit the row height within tolerance.
	 *
	 * @method addItem
	 * @param itemData {Object} Item layout data, containing item aspect ratio.
	 * @return {Boolean} True if successfully added; false if rejected.
	 */

	addItem: function (itemData) {

		var newItems = this.items.concat(itemData),
			// Calculate aspect ratios for items only; exclude spacing
			rowWidthWithoutSpacing = this.width - (newItems.length - 1) * this.spacing,
			newAspectRatio = newItems.reduce(function (sum, item) {
				return sum + item.aspectRatio;
			}, 0),
			targetAspectRatio = rowWidthWithoutSpacing / this.targetRowHeight,
			previousRowWidthWithoutSpacing,
			previousAspectRatio,
			previousTargetAspectRatio;

		// Handle big full-width breakout photos if we're doing them
		if (this.isBreakoutRow) {
			// Only do it if there's no other items in this row
			if (this.items.length === 0) {
				// Only go full width if this photo is a square or landscape
				if (itemData.aspectRatio >= 1) {
					// Close out the row with a full width photo
					this.items.push(itemData);
					this.completeLayout(rowWidthWithoutSpacing / itemData.aspectRatio, 'justify');
					return true;
				}
			}
		}

		if (newAspectRatio < this.minAspectRatio) {

			// New aspect ratio is too narrow / scaled row height is too tall.
			// Accept this item and leave row open for more items.

			this.items.push(merge(itemData));
			return true;

		} else if (newAspectRatio > this.maxAspectRatio) {

			// New aspect ratio is too wide / scaled row height will be too short.
			// Accept item if the resulting aspect ratio is closer to target than it would be without the item.
			// NOTE: Any row that falls into this block will require cropping/padding on individual items.

			if (this.items.length === 0) {

				// When there are no existing items, force acceptance of the new item and complete the layout.
				// This is the pano special case.
				this.items.push(merge(itemData));
				this.completeLayout(rowWidthWithoutSpacing / newAspectRatio, 'justify');
				return true;

			}

			// Calculate width/aspect ratio for row before adding new item
			previousRowWidthWithoutSpacing = this.width - (this.items.length - 1) * this.spacing;
			previousAspectRatio = this.items.reduce(function (sum, item) {
				return sum + item.aspectRatio;
			}, 0);
			previousTargetAspectRatio = previousRowWidthWithoutSpacing / this.targetRowHeight;

			if (Math.abs(newAspectRatio - targetAspectRatio) > Math.abs(previousAspectRatio - previousTargetAspectRatio)) {

				// Row with new item is us farther away from target than row without; complete layout and reject item.
				this.completeLayout(previousRowWidthWithoutSpacing / previousAspectRatio, 'justify');
				return false;

			} else {

				// Row with new item is us closer to target than row without;
				// accept the new item and complete the row layout.
				this.items.push(merge(itemData));
				this.completeLayout(rowWidthWithoutSpacing / newAspectRatio, 'justify');
				return true;

			}

		} else {

			// New aspect ratio / scaled row height is within tolerance;
			// accept the new item and complete the row layout.
			this.items.push(merge(itemData));
			this.completeLayout(rowWidthWithoutSpacing / newAspectRatio, 'justify');
			return true;

		}

	},

	/**
	 * Check if a row has completed its layout.
	 *
	 * @method isLayoutComplete
	 * @return {Boolean} True if complete; false if not.
	 */

	isLayoutComplete: function () {
		return this.height > 0;
	},

	/**
	 * Set row height and compute item geometry from that height.
	 * Will justify items within the row unless instructed not to.
	 *
	 * @method completeLayout
	 * @param newHeight {Number} Set row height to this value.
	 * @param widowLayoutStyle {String} How should widows display? Supported: left | justify | center
	 */

	completeLayout: function (newHeight, widowLayoutStyle) {

		var itemWidthSum = this.left,
			rowWidthWithoutSpacing = this.width - (this.items.length - 1) * this.spacing,
			clampedToNativeRatio,
			clampedHeight,
			errorWidthPerItem,
			roundedCumulativeErrors,
			singleItemGeometry,
			centerOffset;

		// Justify unless explicitly specified otherwise.
		if (typeof widowLayoutStyle === 'undefined' || ['justify', 'center', 'left'].indexOf(widowLayoutStyle) < 0) {
			widowLayoutStyle = 'left';
		}

		// Clamp row height to edge case minimum/maximum.
		clampedHeight = Math.max(this.edgeCaseMinRowHeight, Math.min(newHeight, this.edgeCaseMaxRowHeight));

		if (newHeight !== clampedHeight) {

			// If row height was clamped, the resulting row/item aspect ratio will be off,
			// so force it to fit the width (recalculate aspectRatio to match clamped height).
			// NOTE: this will result in cropping/padding commensurate to the amount of clamping.
			this.height = clampedHeight;
			clampedToNativeRatio = (rowWidthWithoutSpacing / clampedHeight) / (rowWidthWithoutSpacing / newHeight);

		} else {

			// If not clamped, leave ratio at 1.0.
			this.height = newHeight;
			clampedToNativeRatio = 1.0;

		}

		// Compute item geometry based on newHeight.
		this.items.forEach(function (item) {

			item.top = this.top;
			item.width = item.aspectRatio * this.height * clampedToNativeRatio;
			item.height = this.height;

			// Left-to-right.
			// TODO right to left
			// item.left = this.width - itemWidthSum - item.width;
			item.left = itemWidthSum;

			// Increment width.
			itemWidthSum += item.width + this.spacing;

		}, this);

		// If specified, ensure items fill row and distribute error
		// caused by rounding width and height across all items.
		if (widowLayoutStyle === 'justify') {

			itemWidthSum -= (this.spacing + this.left);

			errorWidthPerItem = (itemWidthSum - this.width) / this.items.length;
			roundedCumulativeErrors = this.items.map(function (item, i) {
				return Math.round((i + 1) * errorWidthPerItem);
			});


			if (this.items.length === 1) {

				// For rows with only one item, adjust item width to fill row.
				singleItemGeometry = this.items[0];
				singleItemGeometry.width -= Math.round(errorWidthPerItem);

			} else {

				// For rows with multiple items, adjust item width and shift items to fill the row,
				// while maintaining equal spacing between items in the row.
				this.items.forEach(function (item, i) {
					if (i > 0) {
						item.left -= roundedCumulativeErrors[i - 1];
						item.width -= (roundedCumulativeErrors[i] - roundedCumulativeErrors[i - 1]);
					} else {
						item.width -= roundedCumulativeErrors[i];
					}
				});

			}

		} else if (widowLayoutStyle === 'center') {

			// Center widows
			centerOffset = (this.width - itemWidthSum) / 2;

			this.items.forEach(function (item) {
				item.left += centerOffset + this.spacing;
			}, this);

		}

	},

	/**
	 * Force completion of row layout with current items.
	 *
	 * @method forceComplete
	 * @param fitToWidth {Boolean} Stretch current items to fill the row width.
	 *                             This will likely result in padding.
	 * @param fitToWidth {Number}
	 */

	forceComplete: function (fitToWidth, rowHeight) {

		// TODO Handle fitting to width
		// var rowWidthWithoutSpacing = this.width - (this.items.length - 1) * this.spacing,
		// 	currentAspectRatio = this.items.reduce(function (sum, item) {
		// 		return sum + item.aspectRatio;
		// 	}, 0);

		if (typeof rowHeight === 'number') {

			this.completeLayout(rowHeight, this.widowLayoutStyle);

		} else {

			// Complete using target row height.
			this.completeLayout(this.targetRowHeight, this.widowLayoutStyle);
		}

	},

	/**
	 * Return layout data for items within row.
	 * Note: returns actual list, not a copy.
	 *
	 * @method getItems
	 * @return Layout data for items within row.
	 */

	getItems: function () {
		return this.items;
	}

};

},{"merge":2}],2:[function(require,module,exports){
/*!
 * @name JavaScript/NodeJS Merge v1.2.1
 * @author yeikos
 * @repository https://github.com/yeikos/js.merge

 * Copyright 2014 yeikos - MIT license
 * https://raw.github.com/yeikos/js.merge/master/LICENSE
 */

;(function(isNode) {

	/**
	 * Merge one or more objects 
	 * @param bool? clone
	 * @param mixed,... arguments
	 * @return object
	 */

	var Public = function(clone) {

		return merge(clone === true, false, arguments);

	}, publicName = 'merge';

	/**
	 * Merge two or more objects recursively 
	 * @param bool? clone
	 * @param mixed,... arguments
	 * @return object
	 */

	Public.recursive = function(clone) {

		return merge(clone === true, true, arguments);

	};

	/**
	 * Clone the input removing any reference
	 * @param mixed input
	 * @return mixed
	 */

	Public.clone = function(input) {

		var output = input,
			type = typeOf(input),
			index, size;

		if (type === 'array') {

			output = [];
			size = input.length;

			for (index=0;index<size;++index)

				output[index] = Public.clone(input[index]);

		} else if (type === 'object') {

			output = {};

			for (index in input)

				output[index] = Public.clone(input[index]);

		}

		return output;

	};

	/**
	 * Merge two objects recursively
	 * @param mixed input
	 * @param mixed extend
	 * @return mixed
	 */

	function merge_recursive(base, extend) {

		if (typeOf(base) !== 'object')

			return extend;

		for (var key in extend) {

			if (typeOf(base[key]) === 'object' && typeOf(extend[key]) === 'object') {

				base[key] = merge_recursive(base[key], extend[key]);

			} else {

				base[key] = extend[key];

			}

		}

		return base;

	}

	/**
	 * Merge two or more objects
	 * @param bool clone
	 * @param bool recursive
	 * @param array argv
	 * @return object
	 */

	function merge(clone, recursive, argv) {

		var result = argv[0],
			size = argv.length;

		if (clone || typeOf(result) !== 'object')

			result = {};

		for (var index=0;index<size;++index) {

			var item = argv[index],

				type = typeOf(item);

			if (type !== 'object') continue;

			for (var key in item) {

				if (key === '__proto__') continue;

				var sitem = clone ? Public.clone(item[key]) : item[key];

				if (recursive) {

					result[key] = merge_recursive(result[key], sitem);

				} else {

					result[key] = sitem;

				}

			}

		}

		return result;

	}

	/**
	 * Get type of variable
	 * @param mixed input
	 * @return string
	 *
	 * @see http://jsperf.com/typeofvar
	 */

	function typeOf(input) {

		return ({}).toString.call(input).slice(8, -1).toLowerCase();

	}

	if (isNode) {

		module.exports = Public;

	} else {

		window[publicName] = Public;

	}

})(typeof module === 'object' && module && typeof module.exports === 'object' && module.exports);
},{}],"justified-layout":[function(require,module,exports){
/*!
 * Copyright 2019 SmugMug, Inc.
 * Licensed under the terms of the MIT license. Please see LICENSE file in the project root for terms.
 * @license
 */

'use strict';

var merge = require('merge'),
	Row = require('./row');

/**
 * Create a new, empty row.
 *
 * @method createNewRow
 * @param layoutConfig {Object} The layout configuration
 * @param layoutData {Object} The current state of the layout
 * @return A new, empty row of the type specified by this layout.
 */

function createNewRow(layoutConfig, layoutData) {

	var isBreakoutRow;

	// Work out if this is a full width breakout row
	if (layoutConfig.fullWidthBreakoutRowCadence !== false) {
		if (((layoutData._rows.length + 1) % layoutConfig.fullWidthBreakoutRowCadence) === 0) {
			isBreakoutRow = true;
		}
	}

	return new Row({
		top: layoutData._containerHeight,
		left: layoutConfig.containerPadding.left,
		width: layoutConfig.containerWidth - layoutConfig.containerPadding.left - layoutConfig.containerPadding.right,
		spacing: layoutConfig.boxSpacing.horizontal,
		targetRowHeight: layoutConfig.targetRowHeight,
		targetRowHeightTolerance: layoutConfig.targetRowHeightTolerance,
		edgeCaseMinRowHeight: 0.5 * layoutConfig.targetRowHeight,
		edgeCaseMaxRowHeight: 2 * layoutConfig.targetRowHeight,
		rightToLeft: false,
		isBreakoutRow: isBreakoutRow,
		widowLayoutStyle: layoutConfig.widowLayoutStyle
	});
}

/**
 * Add a completed row to the layout.
 * Note: the row must have already been completed.
 *
 * @method addRow
 * @param layoutConfig {Object} The layout configuration
 * @param layoutData {Object} The current state of the layout
 * @param row {Row} The row to add.
 * @return {Array} Each item added to the row.
 */

function addRow(layoutConfig, layoutData, row) {

	layoutData._rows.push(row);
	layoutData._layoutItems = layoutData._layoutItems.concat(row.getItems());

	// Increment the container height
	layoutData._containerHeight += row.height + layoutConfig.boxSpacing.vertical;

	return row.items;
}

/**
 * Calculate the current layout for all items in the list that require layout.
 * "Layout" means geometry: position within container and size
 *
 * @method computeLayout
 * @param layoutConfig {Object} The layout configuration
 * @param layoutData {Object} The current state of the layout
 * @param itemLayoutData {Array} Array of items to lay out, with data required to lay out each item
 * @return {Object} The newly-calculated layout, containing the new container height, and lists of layout items
 */

function computeLayout(layoutConfig, layoutData, itemLayoutData) {

	var laidOutItems = [],
		itemAdded,
		currentRow,
		nextToLastRowHeight;

	// Apply forced aspect ratio if specified, and set a flag.
	if (layoutConfig.forceAspectRatio) {
		itemLayoutData.forEach(function (itemData) {
			itemData.forcedAspectRatio = true;
			itemData.aspectRatio = layoutConfig.forceAspectRatio;
		});
	}

	// Loop through the items
	itemLayoutData.some(function (itemData, i) {

		if (isNaN(itemData.aspectRatio)) {
			throw new Error("Item " + i + " has an invalid aspect ratio");
		}

		// If not currently building up a row, make a new one.
		if (!currentRow) {
			currentRow = createNewRow(layoutConfig, layoutData);
		}

		// Attempt to add item to the current row.
		itemAdded = currentRow.addItem(itemData);

		if (currentRow.isLayoutComplete()) {

			// Row is filled; add it and start a new one
			laidOutItems = laidOutItems.concat(addRow(layoutConfig, layoutData, currentRow));

			if (layoutData._rows.length >= layoutConfig.maxNumRows) {
				currentRow = null;
				return true;
			}

			currentRow = createNewRow(layoutConfig, layoutData);

			// Item was rejected; add it to its own row
			if (!itemAdded) {

				itemAdded = currentRow.addItem(itemData);

				if (currentRow.isLayoutComplete()) {

					// If the rejected item fills a row on its own, add the row and start another new one
					laidOutItems = laidOutItems.concat(addRow(layoutConfig, layoutData, currentRow));
					if (layoutData._rows.length >= layoutConfig.maxNumRows) {
						currentRow = null;
						return true;
					}
					currentRow = createNewRow(layoutConfig, layoutData);
				}
			}
		}

	});

	// Handle any leftover content (orphans) depending on where they lie
	// in this layout update, and in the total content set.
	if (currentRow && currentRow.getItems().length && layoutConfig.showWidows) {

		// Last page of all content or orphan suppression is suppressed; lay out orphans.
		if (layoutData._rows.length) {

			// Only Match previous row's height if it exists and it isn't a breakout row
			if (layoutData._rows[layoutData._rows.length - 1].isBreakoutRow) {
				nextToLastRowHeight = layoutData._rows[layoutData._rows.length - 1].targetRowHeight;
			} else {
				nextToLastRowHeight = layoutData._rows[layoutData._rows.length - 1].height;
			}

			currentRow.forceComplete(false, nextToLastRowHeight);

		} else {

			// ...else use target height if there is no other row height to reference.
			currentRow.forceComplete(false);

		}

		laidOutItems = laidOutItems.concat(addRow(layoutConfig, layoutData, currentRow));
		layoutConfig._widowCount = currentRow.getItems().length;

	}

	// We need to clean up the bottom container padding
	// First remove the height added for box spacing
	layoutData._containerHeight = layoutData._containerHeight - layoutConfig.boxSpacing.vertical;
	// Then add our bottom container padding
	layoutData._containerHeight = layoutData._containerHeight + layoutConfig.containerPadding.bottom;

	return {
		containerHeight: layoutData._containerHeight,
		widowCount: layoutConfig._widowCount,
		boxes: layoutData._layoutItems
	};

}

/**
 * Takes in a bunch of box data and config. Returns
 * geometry to lay them out in a justified view.
 *
 * @method covertSizesToAspectRatios
 * @param sizes {Array} Array of objects with widths and heights
 * @return {Array} A list of aspect ratios
 */

module.exports = function (input, config) {
	var layoutConfig = {};
	var layoutData = {};

	// Defaults
	var defaults = {
		containerWidth: 1060,
		containerPadding: 10,
		boxSpacing: 10,
		targetRowHeight: 320,
		targetRowHeightTolerance: 0.25,
		maxNumRows: Number.POSITIVE_INFINITY,
		forceAspectRatio: false,
		showWidows: true,
		fullWidthBreakoutRowCadence: false,
		widowLayoutStyle: 'left'
	};

	var containerPadding = {};
	var boxSpacing = {};

	config = config || {};

	// Merge defaults and config passed in
	layoutConfig = merge(defaults, config);

	// Sort out padding and spacing values
	containerPadding.top = (!isNaN(parseFloat(layoutConfig.containerPadding.top))) ? layoutConfig.containerPadding.top : layoutConfig.containerPadding;
	containerPadding.right = (!isNaN(parseFloat(layoutConfig.containerPadding.right))) ? layoutConfig.containerPadding.right : layoutConfig.containerPadding;
	containerPadding.bottom = (!isNaN(parseFloat(layoutConfig.containerPadding.bottom))) ? layoutConfig.containerPadding.bottom : layoutConfig.containerPadding;
	containerPadding.left = (!isNaN(parseFloat(layoutConfig.containerPadding.left))) ? layoutConfig.containerPadding.left : layoutConfig.containerPadding;
	boxSpacing.horizontal = (!isNaN(parseFloat(layoutConfig.boxSpacing.horizontal))) ? layoutConfig.boxSpacing.horizontal : layoutConfig.boxSpacing;
	boxSpacing.vertical = (!isNaN(parseFloat(layoutConfig.boxSpacing.vertical))) ? layoutConfig.boxSpacing.vertical : layoutConfig.boxSpacing;

	layoutConfig.containerPadding = containerPadding;
	layoutConfig.boxSpacing = boxSpacing;

	// Local
	layoutData._layoutItems = [];
	layoutData._awakeItems = [];
	layoutData._inViewportItems = [];
	layoutData._leadingOrphans = [];
	layoutData._trailingOrphans = [];
	layoutData._containerHeight = layoutConfig.containerPadding.top;
	layoutData._rows = [];
	layoutData._orphans = [];
	layoutConfig._widowCount = 0;

	// Convert widths and heights to aspect ratios if we need to
	return computeLayout(layoutConfig, layoutData, input.map(function (item) {
		if (item.width && item.height) {
			return { aspectRatio: item.width / item.height };
		} else {
			return { aspectRatio: item };
		}
	}));
};

},{"./row":1,"merge":2}]},{},[]);
