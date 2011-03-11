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
import urlparse
from app.BeautifulSoup import BeautifulSoup,Comment

import sys
from google.appengine.api import urlfetch
from app.BTSelector import findAll
from app import htmllib
import re
from base import *

class Testme(BaseRequestHandler):
		"""
		this class used for test the feed url,return to us the result
		url:the url which we want to colletc
		start_target:the first filter
		mid_target:the second filter,that tell the system which we want to filter
		end_target:this one tell the system which we want to keep
		"""
		def __init__(self):
				BaseRequestHandler.__init__(self)
				self.current="feedblogtest"
		def dotest(self,url,start_target,mid_target,end_target,allow_target,stop_target=None):
			#try:
				url=urldecode(url)
				page = urlfetch.fetch(url)
				if page.status_code==200:
						result=htmllib.parsehtml(page.content,'test',url,start_target,allow_target,mid_target,end_target,stop_target)
						self.write (result)
				else:
						self.write ('i can not fetch the url,please try!')
			#except:
			#	return False


#valid_tags = u'p i strong b u a h1 h2 h3 br img div embed span'.split()
#valid_attrs = u'src allowscriptaccess allowNetworking pluginspage width allowScriptAccess type wmode height quality invokeurls allownetworking invokeURLs'.split()
