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

__author__ = 'alexliyu2012@gmail.com'

"""Main application file for Wiki example.

Includes:
BasePublicPage - Base class to handle requests
MainHandler - Handles request to TLD
ViewHandler - Handles request to view any wiki entry
UserProfileHandler - Handles request to view any user profile
EditUserProfileHandler - Handles request to edit current user profile
GetUserPhotoHandler - Serves a users image
SendAdminEmail - Handles request to send the admins email
"""

__author__ = 'appengine-support@google.com'

# Python Imports
import datetime
import md5
import os
import sys
import urllib
import urlparse
import wsgiref.handlers
import xml.dom.minidom
import logging

# Google App Engine Imports
from google.appengine.api import images
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import xmpp
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

# Wiki Imports
from markdown import markdown
from model import WikiContent, WikiRevision, WikiUser, WikiSettings
from base import *
from app import acl, pages

# Set the debug level
_DEBUG = True
_ADMIN_EMAIL='alexliyu2012@gmail.com'
_SETTINGS = {
}
class Settings(object):
	def __init__(self):
		self.data = memcache.get('#settings#')
		if not self.data:
			self.data = self.read()
			if not self.data.is_saved():
				defaults = self.defaults()
				for k in defaults:
					if not getattr(self.data, k):
						setattr(self.data, k, defaults[k])
			memcache.set('#settings#', self.data)


	def defaults(self):
		return {
			'title': 'ChinaCDM Wike',
			'start_page': 'welcome',
			'admin_email': 'alexliyu2012@gmail.com',
			'footer': None,
			'pread': True,
			'pwrite': False,
			'owner_meta': None,
			'interwiki': "google = http://www.google.ru/search?sourceid=chrome&ie=UTF-8&q=%s\nwp = http://en.wikipedia.org/wiki/Special:Search?search=%s",
			}

	def read(self):
			tmp = WikiSettings().all().fetch(1)
			if len(tmp):
					return tmp[0]
			else:
					return WikiSettings()

	def dict(self):
			d = {}
			defaults = self.defaults()
			for k in defaults:
					d[k] = getattr(self.data, k)
			return d

	def importFormData(self, r):
			for k in self.defaults():
					if k in ('pread', 'pwrite'):
							nv = bool(r.get(k))
					else:
							nv = r.get(k)
					if nv != getattr(self.data, k):
							setattr(self.data, k, nv)
			self.save()

	def save(self):
			memcache.set('#settings#', self.data)
			self.data.put()

	def get(self, k):
			return getattr(self.data, k)

	def getInterWiki(self):
			interwiki = {}
			if self.data.interwiki:
					m = re.compile('^(\w+)\s+=\s+(.*)$')
					for line in self.data.interwiki.split("\n"):
							mr = m.match(line)
							if mr:
									interwiki[mr.group(1)] = mr.group(2).strip()
			return interwiki
class BasePublicPage(BaseRequestHandler):
  def initialize(self, request, response):
    BaseRequestHandler.initialize(self,request, response)
    self.settings = Settings()
    self.acl = acl.acl(self.settings)
    self.current='wiki'
    values=dict()
    # We check if there is a current user and generate a login or logout URL
    user = users.get_current_user()

    if user:
      log_in_out_url = users.create_logout_url(self.getStartPage())
    else:
      log_in_out_url = users.create_login_url(self.request.path)

    values['settings'] = self.settings.dict()
    values['sidebar'] = pages.cache.get('sidebar', create=True, settings=self.settings)
    url = urlparse.urlparse(self.request.url)
    values['base'] = url[0] + '://' + url[1]
    self.template_vals.update(values)
    # We'll display the user name if available and the URL on all pages
    self.template_vals.update({'user': user, 'log_in_out_url': log_in_out_url, \
				'editing': self.request.get('edit'), \
				'is_admin': users.is_current_user_admin() })

  def handle_exception(self, e, debug_mode):
    if not issubclass(e.__class__, acl.HTTPException):
      return webapp.RequestHandler.handle_exception(self, e, debug_mode)

    if e.code == 401:
      self.redirect(users.create_login_url(self.request.url))
    else:
      self.error(e.code)
      self.wikirender('error.html', {
        'settings': self.settings.dict(),
        'code': e.code,
        'title': e.title,
        'message': e.message,
      })

  def getStartPage(self):
    return '/wiki/' + pages.quote(self.settings.get('start_page'))

  def notifyUser(self, address, message):
    sent = False
    if xmpp.get_presence(address):
      status_code = xmpp.send_message(address, message)
      sent = (status_code != xmpp.NO_ERROR)

  def get_page_cache_key(self, page_name, revision_number=None):
    key = '/wiki/' + page_name
    if revision_number:
      key += '?r=' + str(revision_number)
    return key

  def get_page_name(self, page_title):
    if type(page_title) == type(str()):
      page_title = urllib.unquote(page_title).decode('utf8')
    return page_title.lower().replace(' ', '_')

  def get_current_user(self, back=None):
    if back is None:
      back = self.request.url
    current_user = users.get_current_user()
    if not current_user:
      raise acl.UnauthorizedException()
    return current_user

  def get_wiki_user(self, create=False, back=None):
    current_user = self.get_current_user(back)
    wiki_user = WikiUser.gql('WHERE wiki_user = :1', current_user).get()
    if not wiki_user and create:
      wiki_user = WikiUser(wiki_user=current_user)
      wiki_user.put()
    return wiki_user

  def generateRss(self, template_name, template_values={}):
    url = urlparse.urlparse(self.request.url)
    self.template_vals.update({'self':self.request.url,
				'base':url[0] + '://' + url[1]
				})
    self.response.headers['Content-Type'] = 'text/xml'
    return self.wikirender(template_name, self.template_vals)



class ViewRevisionListHandler(BasePublicPage):

    def get(self, page_title):
        entry = WikiContent.gql('WHERE title = :1', page_title).get()

        if entry:
            revisions = WikiRevision.all()
            # Render the template view_revisionlist.html, which extends base.html
            self.wikirender('view_revisionlist.html', {'page_title': page_title,
                                                        'revisions': revisions,
                                                       })


class ViewDiffHandler(BasePublicPage):

    def get(self, page_title, first_revision, second_revision):
        entry = WikiContent.gql('WHERE title = :1', page_title).get()

        if entry:
            first_revision = WikiRevision.gql('WHERE wiki_page =  :1 '
                                              'AND version_number = :2', entry, int(first_revision)).get()
            second_revision = WikiRevision.gql('WHERE wiki_page =  :1 '
                                              'AND version_number = :2', entry, int(second_revision)).get()

            from app import diff
            body = diff.textDiff(first_revision.revision_body, second_revision.revision_body)

            self.wikirender('view_diff.html',{'page_title': page_title,
                                                             'body': body,
                                                             })


class ViewHandler(BasePublicPage):
  def get_page_content(self, page_title, revision_number=1):
    """When memcache lookup fails, we want to query the information from
       the datastore and return it.  If the data isn't in the data store,
       simply return empty strings
    """
    # Find the wiki entry
    entry = WikiContent.gql('WHERE title = :1', self.get_page_name(page_title)).get()

    if entry:
      # Retrieve the current version
      if revision_number is not None:
          requested_version = WikiRevision.gql('WHERE wiki_page =  :1 '
                                               'AND version_number = :2', entry, int(revision_number)).get()
      else:
          requested_version = WikiRevision.gql('WHERE wiki_page =  :1 '
                                               'ORDER BY version_number DESC', entry).get()
      # Define the body, version number, author email, author nickname
      # and revision date
      body = requested_version.revision_body
      version = requested_version.version_number
      author_email = urllib.quote(requested_version.author.wiki_user.email())
      author_nickname = requested_version.author.wiki_user.nickname()
      version_date = requested_version.created
      # Replace all wiki words with links to those wiki pages
      wiki_body = pages.wikifier(self.settings).wikify(body)
      pread = requested_version.pread
    else:
      # These things do not exist
      wiki_body = ''
      author_email = ''
      author_nickname = ''
      version = ''
      version_date = ''
      pread = False

    return [wiki_body, author_email, author_nickname, version, version_date, pread]

  def get_content(self, page_title, revision_number):
    """Checks memcache for the page.  If the page exists in memcache, it
       returns the information.  If not, it calls get_page_content, gets the
       page content from the datastore and sets the memcache with that info
    """
    page_content = memcache.get(page_title)
    if not page_content:
      page_content = self.get_page_content(page_title, revision_number)

    return page_content

  def get(self, page_name=None):
    if page_name is None or page_name == '':
      page_name = self.settings.get('start_page')
    else:
      page_name = pages.unquote(page_name)

    if self.request.get("edit"):
      return self.get_edit(page_name)
    elif self.request.get("history"):
      return self.get_history(page_name)
    else:
      return self.get_view(page_name)

  def get_view(self, page_name):
	template_values={}

	try:
		template_values['page'],result = pages.cache.get(page_name, self.request.get('r'), nocache=('nc' in self.request.arguments()), settings=self.settings)
	except acl.HTTPException, e:
		template_values['page'] = {
					'name': page_name,
					'error': {
						'code': e.code,
						'message': e.message,
						},
					'body': '<h1>%s</h1><p>%s</p>' % (page_name, e.message),
					'offer_create': True,
					'pread': self.settings.data.pread,
					}
		result=None
	if result:
		self.write(template_values['page'][0])
	else:
		if self.settings.data.pread:
			template_values['page']['pread'] = True

		if 'pread' not in template_values['page'] or not template_values['page']['pread']:
			self.acl.check_read_pages()
		self.template_vals.update(template_values)
		self.wikirender('view.html', self.template_vals)

  def get_edit(self, page_name):
    self.acl.check_edit_pages()
    page = pages.get(pages.unquote(page_name), self.request.get('r'))
    self.wikirender('edit.html', {
      'page': page,
    })

class HistoryHandler(BasePublicPage):
	def get(self):
			self.acl.check_read_pages()
			page_name = self.param('page')
			page = pages.get(page_name)
			history = WikiRevision.gql('WHERE wiki_page = :1 ORDER BY version_number DESC', page).fetch(100)
			self.wikirender('history.html',{'page_name': page_name, 'page_title': page.title, 'revisions': history })

class EditHandler(BasePublicPage):
	def get(self):
		self.acl.check_edit_pages()
		if self.request.get('page'):
				self.template_vals.update({
				'page':pages.get(self.request.get('page'), self.request.get('r'), create=True)})

		self.wikirender('edit.html',self.template_vals)

	def post(self):
		self.acl.check_edit_pages()
		name = self.param('name')
		body = self.param('body')
		title = pages.get_title(pages.wikifier(self.settings).wikify(body))
		if not name:
				name = title

		page = pages.get(name, create=True)
		page.body = body
		page.title = title
		page.author = self.get_wiki_user(True)
		if not page.author and users.get_current_user():
				raise Exception('Could not determine who you are.')
		if self.request.get('pread'):
				page.pread = True
		else:
				page.pread = False
		pages.put(page)

		# Remove old page from cache.
		pages.cache.update(name)



		self.redirect('/wiki/' + pages.quote(page.title))


class UserProfileHandler(BasePublicPage):
  """Allows a user to view another user's profile.  All users are able to
     view this information by requesting http://wikiapp.appspot.com/user/*
  """

  def get(self, user):
    """When requesting the URL, we find out that user's WikiUser information.
       We also retrieve articles written by the user
    """
    # Webob over quotes the request URI, so we have to unquote twice
    unescaped_user = urllib.unquote(urllib.unquote(user))

    # Query for the user information
    wiki_user_object = users.User(unescaped_user)
    wiki_user = WikiUser.gql('WHERE wiki_user = :1', wiki_user_object).get()

    # Retrieve the unique set of articles the user has revised
    # Please note that this doesn't gaurentee that user's revision is
    # live on the wiki page
    article_list = []
    for article in wiki_user.wikirevision_set:
      article_list.append(article.wiki_page.title)
    articles = set(article_list)

    # If the user has specified a feed, fetch it
    feed_content = ''
    feed_titles = []
    if wiki_user.user_feed:
      feed = urlfetch.fetch(wiki_user.user_feed)
      # If the fetch is a success, get the blog article titles
      if feed.status_code == 200:
        feed_content = feed.content
        xml_content = xml.dom.minidom.parseString(feed_content)
        for title in xml_content.getElementsByTagName('title'):
          feed_titles.append(title.childNodes[0].nodeValue)
    # Generate the user profile
    self.wikirender('user.html',{'queried_user': wiki_user,
                                                'articles': articles,
                                                'titles': feed_titles})

class EditUserProfileHandler(BasePublicPage):
  """This allows a user to edit his or her wiki profile.  The user can upload
     a picture and set a feed URL for personal data
  """
  def get(self, user):
    # Get the user information
    unescaped_user = urllib.unquote(user)
    wiki_user_object = users.User(unescaped_user)
    # Only that user can edit his or her profile
    if users.get_current_user() != wiki_user_object:
      self.redirect(self.getStartPage())

    wiki_user = WikiUser.gql('WHERE wiki_user = :1', wiki_user_object).get()
    if not wiki_user:
      wiki_user = WikiUser(wiki_user=wiki_user_object)
      wiki_user.put()

    article_list = []
    for article in wiki_user.wikirevision_set:
      article_list.append(article.wiki_page.title)
    articles = set(article_list)
    self.wikirender('edit_user.html',{'queried_user': wiki_user,
                                                     'articles': articles})

  def post(self, user):
    # Get the user information
    unescaped_user = urllib.unquote(user)
    wiki_user_object = users.User(unescaped_user)
    # Only that user can edit his or her profile
    if users.get_current_user() != wiki_user_object:
      self.redirect(self.getStartPage())

    wiki_user = WikiUser.gql('WHERE wiki_user = :1', wiki_user_object).get()

    user_photo = self.request.get('user_picture')
    if user_photo:
      raw_photo = images.Image(user_photo)
      raw_photo.resize(width=256, height=256)
      raw_photo.im_feeling_lucky()
      wiki_user.wiki_user_picture = raw_photo.execute_transforms(output_encoding=images.PNG)
    feed_url = self.request.get('feed_url')
    if feed_url:
      wiki_user.user_feed = feed_url

    wiki_user.put()


    self.redirect('/user/%s' % user)


class GetUserPhotoHandler(BasePublicPage):
  """This is a class that handles serving the image for a user

     The template requests /getphoto/example@test.com and the handler
     retrieves the photo from the datastore, sents the content-type
     and returns the photo
  """

  def get(self, user):
    unescaped_user = urllib.unquote(user)
    wiki_user_object = users.User(unescaped_user)
    # Only that user can edit his or her profile
    if users.get_current_user() != wiki_user_object:
      self.redirect(self.getStartPage())

    wiki_user = WikiUser.gql('WHERE wiki_user = :1', wiki_user_object).get()

    if wiki_user.wiki_user_picture:
      self.response.headers['Content-Type'] = 'image/jpg'
      self.response.out.write(wiki_user.wiki_user_picture)


class SendAdminEmail(BasePublicPage):
  """Sends the admin email.

     The user must be signed in to send email to the admins
  """
  def get(self):
    # Check to see if the user is signed in
    current_user = users.get_current_user()

    if not current_user:
      self.redirect(users.create_login_url('/sendadminemail'))

    # Generate the email form
    self.wikirender('admin_email.html')

  def post(self):
    # Check to see if the user is signed in
    current_user = users.get_current_user()

    if not current_user:
      self.redirect(users.create_login_url('/sendadminemail'))

    # Get the email subject and body
    subject = self.request.get('subject')
    body = self.request.get('body')

    # send the email
    mail.send_mail_to_admins(sender=current_user.email(), reply_to=current_user.email(),
                             subject=subject, body=body)

    # Generate the confirmation template
    self.wikirender('confirm_email.html')

class UsersHandler(BasePublicPage):
  def get(self):
    self.acl.check_edit_settings()

    users = [{
      'name': user.wiki_user.nickname(),
      'email': user.wiki_user.email(),
      'md5': md5.new(user.wiki_user.email()).hexdigest(),
      'joined': user.joined,
      } for user in WikiUser.gql('ORDER BY wiki_user').fetch(1000)]

    self.wikirender('users.html',{'users': users })

  def post(self):
    self.acl.check_edit_settings()
    email = self.request.get('email').strip()
    if email and not WikiUser.gql('WHERE wiki_user = :1', users.User(email)).get():
      user = WikiUser(wiki_user=users.User(email))
      user.put()
    self.redirect('/w/users')

class IndexHandler(BasePublicPage):
  def get(self):
    self.acl.check_read_pages()

    if '.rss' == self.request.path[-4:]:
      plist = {}
      for revision in WikiRevision.gql('ORDER BY created DESC').fetch(1000):
        page = revision.wiki_page.title
        if page not in plist:
          plist[page] = { 'name': page, 'title': self.get_page_name(page), 'created': revision.created, 'author': revision.author }
      self.generateRss('index-rss.html',{
        'items': [plist[page] for page in plist],
      });
    else:
      self.wikirender('index.html',{'pages': [{
        'name': page.title,
        'uri': '/wiki/' + pages.quote(page.title),
      } for page in WikiContent.gql('ORDER BY title').fetch(1000)] })

class ChangesHandler(BasePublicPage):
  def get(self):
    self.acl.check_read_pages()

    if '.rss' == self.request.path[-4:]:
      self.generateRss('changes-rss.html', template_values={
        'changes': WikiContent.gql('ORDER BY updated DESC').fetch(1000),
      })
    else:
      content = memcache.get('/w/changes')
      if not content or self.request.get('nc'):
        template_values={
          'self': self.request.url,
          'changes': WikiContent.gql('ORDER BY updated DESC').fetch(1000),
        }
        content = self.wikirender('changes.html', template_values)
        memcache.set('/w/changes', content)

      self.response.out.write(content)

class InterwikiHandler(BasePublicPage):
  def get(self):
    self.acl.check_edit_pages()
    items = self.settings.getInterWiki()
    self.wikirender('interwiki.html',{'iwlist': [{'key': k, 'host': urlparse.urlparse(items[k])[1], 'sample': items[k].replace('%s', 'hello%2C%20world')} for k in sorted(items.keys())]})

class SettingsHandler(BasePublicPage):
  def get(self):
    self.acl.check_edit_settings()
    self.wikirender('settings.html',{
      'settings': self.settings.dict(),
    })

  def post(self):
    self.settings.importFormData(self.request)
    self.response.set_status(303)
    self.redirect('/w/settings')

class UpgradeHandler(BasePublicPage):
  def get(self):
    self.acl.check_edit_settings()

    for page in WikiContent.all().fetch(1000):
      if page.updated is None or page.author is None or page.body is None:
        rev = WikiRevision.gql('WHERE wiki_page = :1 ORDER BY version_number DESC', page).get()
        if rev is not None:
          page.updated = rev.created
          page.author = rev.author
          page.pread = rev.pread
          page.body = rev.revision_body
          page.put()
      elif '_' in page.title:
        page.title = page.title.replace('_', ' ')
        page.put()

    self.redirect('/w/index')


_WIKI_URLS = [('/wiki', ViewHandler),
              ('/wiki/', ViewHandler),
              ('/w/changes(?:\.rss)?', ChangesHandler),
              ('/w/edit', EditHandler),
              ('/w/history', HistoryHandler),
              ('/w/index(?:\.rss)?', IndexHandler),
              ('/w/interwiki', InterwikiHandler),
              ('/w/users', UsersHandler),
	      ('/users/(.*)', ViewHandler),
              ('/w/upgrade', UpgradeHandler),
              ('/w/settings', SettingsHandler),
              ('/wiki/(.+)', ViewHandler)
              ]

def main():
  _DEBUG = ('Development/' in os.environ.get('SERVER_SOFTWARE'))
  if _DEBUG:
    logging.getLogger().setLevel(logging.DEBUG)
  application = webapp.WSGIApplication(_WIKI_URLS, debug=_DEBUG)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
