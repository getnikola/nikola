#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Date Conditionals v0.1.6
# Copyright © 2015-2017, Chris Warrick.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the author of this software nor the names of
#    contributors to this software may be used to endorse or promote
#    products derived from this software without specific prior written
#    consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Date range parser."""

from __future__ import print_function, unicode_literals
import datetime
import dateutil.parser
import re
import operator


__all__ = ('date_in_range',)
CLAUSE = re.compile('(year|month|day|hour|minute|second|weekday|isoweekday)?'
                    ' ?(==|!=|<=|>=|<|>) ?(.*)')
OPERATORS = {
    '==': operator.eq,
    '!=': operator.ne,
    '<=': operator.le,
    '>=': operator.ge,
    '<': operator.lt,
    '>': operator.gt,
}


def date_in_range(date_range, date, debug=False, now=None):
    """Check if date is in the range specified.

    Format:
    * comma-separated clauses (AND)
    * clause: attribute comparison_operator value (spaces optional)
        * attribute: year, month, day, hour, month, second, weekday, isoweekday
          or empty for full datetime
        * comparison_operator: == != <= >= < >
        * value: integer, 'now' or dateutil-compatible date input

    The optional `now` parameter can be used to provide a specific `now` value
    (if none is provided, datetime.datetime.now() is used).
    """
    out = True

    for item in date_range.split(','):
        attribute, comparison_operator, value = CLAUSE.match(
            item.strip()).groups()
        if attribute in ('weekday', 'isoweekday'):
            left = getattr(date, attribute)()
            right = int(value)
        elif attribute:
            left = getattr(date, attribute)
            right = int(value)
        elif value == 'now':
            left = date
            right = now or datetime.datetime.now()
        else:
            left = date
            right = dateutil.parser.parse(value)
        if debug:  # pragma: no cover
            print("    <{0} {1} {2}>".format(left, comparison_operator, right))
        out = out and OPERATORS[comparison_operator](left, right)
    return out
