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
# Copyright Š 2010 alexliyu

import logging
from google.appengine.ext import webapp
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch_errors import DownloadError
from app import htmllib
import feedparser

theresult=[]

def getresult(feed_url, target):
        feed_test=feed_url[0]
        feed_target=target[0]
        result=''
        theresult=[]
        try:
            result = urlfetch.fetch(feed_test)
        except DownloadError, error:
            print('Could not get feed %s - %s' % (feed_target, error.message))
        if result.status_code == 200:
            try:
                parsefeed(result.content, feed_test, feed_target )
                return theresult
            except:
                return None
        elif result.status_code == 500:
            print('Feed %s returned with status code 500.' % feed_test)
        elif result.status_code == 404:
            print('Error 404: Nothing found at %s.' % feed_test)

def parsefeed(feed_content, feed_url, feed_target):
        feed = feedparser.parse(feed_content)
        rpcs = []
        for entry in feed.entries:
            url=''
            if(entry.has_key('feedburner_origlink')):
                url = entry.feedburner_origlink
            else:
                url = entry.link
            rpc = urlfetch.create_rpc()
            rpc.callback = __create_callback( rpc, entry, feed_url, url, feed_target)
            urlfetch.make_fetch_call(rpc, url)
            rpcs.append(rpc)

# Finish all RPCs, and let callbacks process the results.
        for rpc in rpcs:
            rpc.wait()

def handle_result(rpc, entry, feed_url, url, feed_target):
        try:
            result = rpc.get_result()
            if result.status_code == 200:
                contenthtml=htmllib.parsehtml(result.content, feed_url, feed_target)


                if contenthtml!=None:
                    theresult.append([contenthtml])

                else:
                    print ('something is wrong at %s,the feed is %s,the target is %s ,please check,the call back result is none', url,feed_url, feed_target)
        except Exception,Error:
            logging.debug ('DownloadError in get  %s.' %url)




# Use a helper function to define the scope of the callback.
def __create_callback(rpc, entry, feed_url, url, feed_target):
        return lambda: handle_result(rpc, entry, feed_url, url, feed_target)
