// This script does pagination for content in the div inside of `div.e-content' of a post
// It does as follows:
//   * adds the pagination navigator items at top at bottom
//   * separates the content into pages
//      * based on a set number (10) of paragraphs ('p'-elements)
//      * Not sure best way to parameterize this
//   * adds a function which will handle future page changes
// It paginates the content based on a set number (10) of paragraphs ( 'p'-elements )
// To use in Nikola:
//   * Include this script is included at the bottom of whichever template you are using
//      * e.g. <script type="text/javascript" src="../../assets/js/nikola-pagination.js"></script>
//      * make sure dependencies are also added
//   * The content to be paginated must be:
//      * all children of the div below the parent `div.e-content'.
//   * see sample template `paginated-post.tmpl'
// Dependencies:
//    * jquery
//    * simplePagination
// Notes:
//    * Not sure best way to parameterize the amount of content per page
//    * Currently, changing pages causes jumping to an anchor at the top of the page, little annoying
//

// Get the full entry-content of the post
var full_entry_content = $("div.e-content");

var p_per_page = 10; // Number of paragraphs on a given page; Should be parameterized somehow

// Store an array of each page of information, adjusting `current_page' object as needed
pagination_target = $("div.e-content div")
pagination_target.attr("id", "paginated-content")
var all_pages = paginateContent("#paginated-content", p_per_page); // all content pages

// Add in pagination element at the top and bottom
full_entry_content.prepend('<div id="pagination-container-top" class="simple-pagination"></div>');
full_entry_content.append('<div id="pagination-container-bottom" class="simple-pagination"></div>');
var pagination_top = $("#pagination-container-top"); // The pagination-selector at the top of the pag
var pagination_bottom = $("#pagination-container-bottom"); // The pagination-selector at the bottom of page

num_pages = all_pages.length;
pagination_top.pagination({
   pages: num_pages,
   cssStyle: 'light-theme'});

pagination_bottom.pagination({
   pages: num_pages,
   cssStyle: 'light-theme'});
// Check whether the page has been explicitly provided in the URL
anchor_target = window.location.href.split("#")[1];
if ( anchor_target ) {
    pagenum = anchor_target.replace(/^page-([\d]+)$/, '\$1');
    if (pagenum) {
	selectPage("#paginated-content", Number(pagenum), all_pages);
    } else {
	// Start by displaying page number 1
	selectPage("#paginated-content", 1, all_pages);
    }
} else {
    // If no anchor provided, load page 1
    // Start by displaying page number 1
    selectPage("#paginated-content", 1, all_pages);
}

// When paginated portion is clicked, change the current page to the clicked one
$(document).on("click", ".page-link", function(){
    if (isNaN(this.text) ){
	// Use the href value to get the target page number
	// Note: had tried using $(this).closest("div") to get the parent pagination container,
	// but for some reason this was failing and returning 'undefined'
	// If the parent div ('#pagination-container-top' or '#pagination-container-bottom')
	// could be used, then the appropriate pagination('currentPage') property can be used
	// Since attempts to use this failed though, just using the href of the clicked element
	target_pagenum = Number(this.href.split("#")[1].split("-")[1]);
	selectPage( "#paginated-content", target_pagenum, all_pages );
    } else {
	selectPage( "#paginated-content", Number(this.text), all_pages);
    }
});

function selectPage( identifier, targetPage, page_list ) {
    // Change the pagination navigators at top and bottom;
    // also update the content of the element with the given identifier
    // The content will become the 1-indexed page of the page_list variable
    pagination_top.pagination('selectPage', targetPage);
    pagination_bottom.pagination('selectPage', targetPage);
    $(identifier).html( page_list[ targetPage - 1 ]);    
}


function paginateContent( identifier, paragraphs_per_page ) {
    // Paginate content of the given identifier, with the paragraps_per_page number
    // Any straggling elements after the last p-element will be included on the final page
    // Other non-p elements will go on the same page as the following p-element 
    all_pages = [];
    page_i = 1;
    stored_paragraphs = 0;
    leftovers = [];
    current_page = $('<div id="page-1"></div>');
    $(identifier).children().each( function() {
	current_page.append($(this));
    	if ( $(this).prop('nodeName') == "P" ) {
    	    // Increase the count of stored paragraphs, until it meets the paragraphs per page count
    	    stored_paragraphs += 1;
    	    if ( stored_paragraphs % paragraphs_per_page == 0 ) {
    		// The page is complete. Prepend the page anchor, and start building onto 
    		page_anchor = $('<a href="#page-' + page_i.toString() + '"/>');
    		current_page.prepend(page_anchor);
    		// Push the newly completed page into the list of all pages, and increment
    		all_pages.push(current_page);
    		page_i++;    
    		//console.log("Current page ("+page_i+"): "+current_page.html());
    		current_page = $('<div id="page-'+page_i.toString() +'"></div>');
    	    }
    	}	
    });
    // Check for straggler elements in the final page which should be added into the last page
    // Add them into the final page
    non_p_closers = current_page.children(":not(p)");
    non_p_closers.each( function() {
    	all_pages[ all_pages.length - 1 ].append($(this));
    });
    return all_pages;
}
