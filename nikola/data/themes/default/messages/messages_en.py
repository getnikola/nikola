from __future__ import unicode_literals

MESSAGES = [
    "Posts for year %s",
    "Archive",
    "Posts about %s",
    "Tags",
    "Also available in",
    "More posts about",
    "Posted",
    "Original site",
    "Read in English",
    "Newer posts",
    "Older posts",
    "Previous post",
    "Next post",
    "old posts page %d",
    "Read more",
    "Source",
]

# In english things are not translated
msg_dict = {}
for msg in MESSAGES:
    msg_dict[msg] = msg
MESSAGES = msg_dict
MESSAGES["LANGUAGE"] = "English"
