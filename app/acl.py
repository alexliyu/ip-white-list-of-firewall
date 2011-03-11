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

# GAE imports
from google.appengine.api import users

# gaewiki imports
from model import WikiUser

class HTTPException(Exception):
  pass

class UnauthorizedException(HTTPException):
  def __init__(self):
    self.code = 401
    self.title = 'Unauthorized'
    self.message = 'Please log in and come back.'

class ForbiddenException(HTTPException):
  def __init__(self):
    self.code = 403
    self.title = 'Forbidden'
    self.message = 'You don\'t have access to this page.'

class acl(object):
  def __init__(self, settings):
    self.settings = settings

  def can_read_pages(self):
    """
    Returns True if the user can read pages, otherwise throws an exception.
    """
    if self.can_edit_settings():
      return True
    if self.settings.get('pread'):
      return True
    cu = users.get_current_user()
    if not cu:
      raise UnauthorizedException()
    wu = WikiUser.gql('WHERE wiki_user = :1', cu).get()
    if not wu:
      raise ForbiddenException()
    return True

  def check_read_pages(self):
    self.check_wrapper(self.can_read_pages)

  def can_edit_pages(self):
    """
    Returns True if the user can edit pages, otherwise throws an exception."
    """
    if self.can_edit_settings():
      return True
    if self.settings.get('pwrite'):
      return True
    cu = users.get_current_user()
    if not cu:
      raise UnauthorizedException()
    wu = WikiUser.gql('WHERE wiki_user = :1', cu).get()
    if not wu:
      raise ForbiddenException()
    return True

  def check_edit_pages(self):
    self.check_wrapper(self.can_edit_pages)

  def can_edit_settings(self):
    """
    Returns True if the user can edit wiki settings.
    """
    return users.is_current_user_admin()

  def check_edit_settings(self):
    self.check_wrapper(self.can_edit_settings)

  def check_wrapper(self, cb):
    """
    Raises an appropriate exception if the callback function returns Fallse.
    """
    if not cb():
      if users.get_current_user():
        raise ForbiddenException()
      else:
        raise UnauthorizedException()
