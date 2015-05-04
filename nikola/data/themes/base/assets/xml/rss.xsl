<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/" version="1.0">
<xsl:output method="xml"/>
<xsl:template match="/">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width"/>
<title><xsl:value-of select="rss/channel/title"/> (RSS)</title>
<style><![CDATA[html{margin:0;padding:0;}body{color:hsl(180,1%,31%);font-family:Helvetica,Arial,sans-serif;font-size:17px;line-height:1.4;margin:5%;max-width:35rem;padding:0;}input{min-width:20rem;margin-left:.2rem;padding-left:.2rem;padding-right:.2rem;}ol{list-style-type:disc;padding-left:1rem;}h2{font-size:22px;font-weight:inherit;}]]></style>
</head>
<body>
<h1><xsl:value-of select="rss/channel/title"/> (RSS)</h1>
<p>This is an <abbr title="Really Simple Syndication">RSS</abbr> feed. To subscribe to it, copy its address and paste it when your feed reader asks for it. It will be updated periodically in your reader. New to feeds? <a href="https://duckduckgo.com/?q=how+to+get+started+with+rss+feeds" title="Search on the web to learn more">Learn more</a>.</p>
<p>
<label for="address">RSS address:</label>
<input><xsl:attribute name="id">address</xsl:attribute><xsl:attribute name="spellcheck">false</xsl:attribute><xsl:attribute name="value"><xsl:value-of select="rss/channel/atom:link[@rel='self']/@href"/></xsl:attribute></input>
</p>
<p>Preview of the feed’s current headlines:</p>
<ol>
<xsl:for-each select="rss/channel/item">
<li><h2><a><xsl:attribute name="href"><xsl:value-of select="link"/></xsl:attribute><xsl:value-of select="title"/></a></h2></li>
</xsl:for-each>
</ol>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
