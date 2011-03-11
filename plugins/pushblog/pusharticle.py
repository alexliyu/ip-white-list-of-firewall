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
#  Copyright Š 2010 alexliyu email:alexliyu2012@gmail.com
from cdm_plugin import *
from model import Entry
from pushmodel import PushList, PushMethod
from base import *

class Pusharticle(BaseRequestHandler):

		def __init__(self):
				BaseRequestHandler.__init__(self)
				self.current="pusharticle"


		def Push(self,page=None,*arg1,**arg2):
				listits = PushList().all()
				logging.info('start to Push Article')
				for pushitem in listits:
						push_retrieval_deadline = datetime.now()-timedelta(minutes = pushitem.pushtime)
						if pushitem.last_retrieved > push_retrieval_deadline:
							logging.info('Skipping entry %s.',pushitem.name)
							continue
						try:
								if pushitem.latest:
										entry=Entry().all().filter('categorie_keys = ',db.Key(pushitem.category)).filter('date > ',pushitem.latest).order('date').fetch(1)[0]
								else:
										entry=Entry().all().filter('categorie_keys = ',db.Key(pushitem.category)).order('date').fetch(1)[0]
						except:
								entry=None
						if entry:

								logging.info('Getting entry %s.',entry.title)
								kwargs=dict((['model',entry],
										['pushitem',pushitem]
										))
								result=PushMethod().Get_Method(pushitem.pushurl,**kwargs)
								if result:
										logging.info('Pushed Successful')
								else:
										logging.info('Pushed Fail')

						else:
								logging.info('no entry')
