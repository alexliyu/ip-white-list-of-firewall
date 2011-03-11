#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Copyright Š 2010 alexliyu email:alexliyu2012@gmail.com
# This file is part of CDM SYSTEM.
#
# CDM SYSTEM is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 0.3 of the License, or (at your option) any later
# version. WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# CDM SYSTEM. If not, see <http://www.gnu.org/licenses/>.
import logging
from django import template
from model import *
import  django.template.defaultfilters as defaultfilters
import urllib
register = template.Library()
from datetime import *

@register.filter
def datetz(date,format):  #datetime with timedelta
    t=timedelta(seconds=3600*g_blog.timedelta)
    return defaultfilters.date(date+t,format)

@register.filter
def TimestampISO8601(t):
    """Seconds since epoch (1970-01-01) --> ISO 8601 time string."""
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(t))

@register.filter
def urlencode(value):
    return urllib.quote(value.encode('utf8'))
#TODO the filter is used for fetch,the ex:{%for i in cms.Entry|Fetchorder:"-date"|Fetchcount:3%}
@register.filter
def Fetchcount(v1,v2):
	try:
		return v1.fetch(v2)
	except:
		pass
#TODO the filter is used for order
@register.filter
def Fetchorder(v1,v2):
	try:
		return v1.order(v2)
	except:
		pass

#TODO this filter is used for filter which have the images in content
@register.filter
def Fetchimages(v1):
	return v1.filter('imageurl != ',None)

#TODO this filter is used for show the image ,the b is mean big and the s is small
@register.filter
def Showimage(v1,v2):
	if v2 =='b':
		return v1.Images()
	else:
		return v1.Simages()

#TODO this filter is used for show the custom filter
@register.filter
def Fetchcats(v1,v2):
	try:
		thekey=Entry().Fetchcats(v2)
		return v1.filter('categorie_keys = ',thekey)
	except:
		pass


#TODO this filter is used for filter which's sticky is true
@register.filter
def Fetchsticky(v1):
	return v1.filter('sticky == ',True)


@register.filter
def check_current(v1,v2):
    if v1==v2:
        return "current"
    else:
        return ""

@register.filter
def excerpt_more(entry,value='..more'):
    return entry.get_content_excerpt(value.decode('utf8'))

@register.filter
def dict_value(v1,v2):
    return v1[v2]


from app.html_filter import html_filter

plog_filter = html_filter()
plog_filter.allowed = {
        'a': ('href', 'target', 'name'),
        'b': (),
        'blockquote': (),
        'pre': (),
        'em': (),
        'i': (),
        'img': ('src', 'width', 'height', 'alt', 'title'),
        'strong': (),
        'u': (),
        'font': ('color', 'size'),
        'p': (),
        'h1': (),
        'h2': (),
        'h3': (),
        'h4': (),
        'h5': (),
        'h6': (),
        'table': (),
        'tr': (),
        'th': (),
        'td': (),
        'ul': (),
        'ol': (),
        'li': (),
        'br': (),
        'hr': (),
        }

plog_filter.no_close += ('br',)
plog_filter.allowed_entities += ('nbsp','ldquo', 'rdquo', 'hellip',)
plog_filter.make_clickable_urls = False # enable this will get a bug about a and img

@register.filter
def do_filter(data):
    return plog_filter.go(data)

'''
tag like {%mf header%}xxx xxx{%endmf%}
'''
@register.tag("mf")
def do_mf(parser, token):
    nodelist = parser.parse(('endmf',))
    parser.delete_first_token()
    return MfNode(nodelist,token)

class MfNode(template.Node):
    def __init__(self, nodelist,token):
        self.nodelist = nodelist
        self.token=token

    def render(self, context):
        tokens= self.token.split_contents()
        if len(tokens)<2:
            raise TemplateSyntaxError, "'mf' tag takes one argument: the filter name is needed"
        fname=tokens[1]
        output = self.nodelist.render(context)
        return g_blog.tigger_filter(fname,output)
