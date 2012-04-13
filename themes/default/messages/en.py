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
]

# In english things are not translated
msg_dict = {}
for msg in MESSAGES:
    msg_dict[msg] = msg
MESSAGES = msg_dict
MESSAGES[u"LANGUAGE"] = "English"
