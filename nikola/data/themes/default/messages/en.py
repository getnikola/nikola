MESSAGES = [
    u"Posts for year %s",
    u"Archive",
    u"Posts about %s:",
    u"Tags",
    u"Also available in: ",
    u"More posts about",
    u"Posted:",
    u"Original site",
    u"Read in english",
    u"&larr; Newer posts",
    u"Older posts &rarr;",
    u"&larr; Previous post",
    u"Next post &rarr;",
]

# In english things are not translated
msg_dict = {}
for msg in MESSAGES:
    msg_dict[msg] = msg
MESSAGES = msg_dict
MESSAGES[u"LANGUAGE"] = "English"
