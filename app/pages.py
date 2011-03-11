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

# Python imports
import logging, re, urllib

# GAE imports
from google.appengine.api import memcache

# Wiki imports
from model import WikiContent, WikiRevision
import markdown
from app import acl

# Regular expression for a wiki word.  Wiki words are all letters
# As well as camel case.  For example: WikiWord
_WIKI_WORD = re.compile('\[\[([^]|]+\|)?([^]]+)\]\]')

class NotFoundException(acl.HTTPException):
  def __init__(self):
    self.code = 404
    self.title = 'Not Found'
    self.message = 'There is no such page.'

def get(name, revision=None, create=False):
	page = WikiContent.gql('WHERE title = :1', name).get()
	if not page:
		if create:
				return WikiContent(title=name)
		raise NotFoundException()
	if revision:
		return WikiRevision.gql('WHERE wiki_page = :1 AND version_number = :2', page, int(revision)).get()
	return page

def put(page):
	page.put()
	revision=WikiRevision.all().filter('wiki_page = ',page).order('-version_number').fetch(1)
	if revision:
			revision_num=revision[0].version_number+1
	else:
			revision_num=1
	revision=WikiRevision(wiki_page=page,
				revision_body = page.body,
				author = page.author,
				created = page.updated,
				version_number = revision_num,
				pread = page.pread)
	#revision.wiki_page=page
	#revision.revision_body = page.body
	#revision.author = page.author
	#revision.created = page.updated
	#revision.version_number = revision_num
	#revision.pread = page.pread
	revision.put()

	cache.update(page.title)

def unquote(name):
  return urllib.unquote(name).decode('utf8').replace('_', ' ')

def quote(name, underscore=True):
  if underscore:
    name = name.replace(' ', '_')
  return urllib.quote(name.encode('utf8'))

def get_title(text):
  r = re.search("<h1>(.*)</h1>", text)
  if r:
    return r.group(1)

class wikifier:
  def __init__(self, settings):
    self.settings = settings
    self.interwiki = settings.getInterWiki()

  def wikify(self, text):
    """
    Applies wiki markup to raw markdown text.
    """
    if text is not None:
      text, count = _WIKI_WORD.subn(self.wikify_one, text)
      text = markdown.markdown.markdown(text).strip()
    return text

  def wikify_one(self, pat):
    page_title = pat.group(2)
    if pat.group(1):
      page_name = pat.group(1).rstrip('|')
    else:
      page_name = page_title

    # interwiki
    if ':' in page_name:
      parts = page_name.split(':', 2)
      if page_name == page_title:
        page_title = parts[1]
      if parts[0] in self.interwiki:
        return '<a class="iw iw-%s" href="%s" target="_blank">%s</a>' % (parts[0], self.interwiki[parts[0]].replace('%s', urllib.quote(parts[1].encode('utf8'))), page_title)
      else:
        return '<a title="Unsupported interwiki was used (%s)." class="iw-broken">%s</a>' % (urllib.quote(parts[0]), page_title)

    return '<a class="int" href="%s">%s</a>' % (quote(page_name), page_title)

class cache:
	@classmethod
	def get(cls, name, revision=None, nocache=False, create=False, settings=None):
			key = cls.get_key(name, revision)
			value = memcache.get(key)
			result=True
			if nocache or value is None:
			  result=False
			  page = get(name, revision, create=create)
			  if not revision:
				value = {
					'name': name,
					'body': wikifier(settings).wikify(page.body),
					'author': None,
					'author_email': None,
					'updated': page.updated,
					'pread': page.pread,
					}
			  else:
				value = {
					'name': name,
					'body': wikifier(settings).wikify(page.revision_body),
					'author': None,
					'author_email': None,
					'updated': page.created,
					'pread': page.pread,
					}
			  if page.author:
				value['author'] = page.author.wiki_user.nickname()
				value['author_email'] = page.author.wiki_user.email()
			return value,result

	@classmethod
	def get_key(cls, name, revision):
			key = '/wiki/' + name
			if revision:
					key += '?r=' + str(revision)
			return key

	@classmethod
	def update(cls, name):
			memcache.delete(cls.get_key(name, None))
			memcache.delete('/w/edit?page=%s'% name)
