A "website-done-with-bootstrap" theme, so to speak. 

Has a fixed navigation bar at top that displays the NAVIGATION_LINKS
setting and supports nested menus.

This theme is used in Nikola's website: http://getnikola.com

Important: To fit in the bootstrap navigation bar, the search form needs the
navbar-form and pull-left CSS classes applied. Here is an example with Nikola's
default duckduckgo search form:

    SEARCH_FORM = """
        <!-- Custom search -->
        <form method="get" id="search" action="http://duckduckgo.com/" class="navbar-form pull-left">
            <input type="hidden" name="sites" value="%s"/>
            <input type="hidden" name="k8" value="#444444"/>
            <input type="hidden" name="k9" value="#D51920"/>
            <input type="hidden" name="kt" value="h"/>
            <input type="text" name="q" maxlength="255" placeholder="Search&hellip;" class="span2" style="margin-top: 4px;"/>
            <input type="submit" value="DuckDuckGo Search" style="visibility: hidden;" />
        </form>
        <!-- End of custom search -->
    """ % SITE_URL
