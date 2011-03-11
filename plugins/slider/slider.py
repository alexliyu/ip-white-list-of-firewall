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
import logging
from model import *
from google.appengine.api import users
import re
class slider(Plugin):
    def __init__(self):
        Plugin.__init__(self,__file__)
        self.author="李昱"
        self.authoruri="http://www.51203344.tk"
        self.uri="http://www.51203344.tk"
        self.description="PageSlider Plugin."
        self.name="PageSlider Plugin"
        self.version="0.1"
       # self.register_filter('slider',self.slider)


    def slider(self,content,blog=None,*arg1,**arg2):

        contenthtml=''
        content= '''
                <ul id="fader">
               '''

        entries = Entry.all().filter('entrytype =','page').\
                filter("published =", True).order('-date').\
                filter("sticky =",True).\
                fetch(5)
        for entry in entries:
                if self.isphoto(entry.content)!=None:
                        logging.info(self.isphoto(entry.content))
                        contenttitle=entry.title
                        contentexcerpt=entry.excerpt
                        contentauthorname=entry.author_name
                        contentlink=entry.link
                        contentdate=str(entry.monthyear)
                        contentimages=str(self.isphoto(entry.content))
                        contenthtml+='''
                    <li>
                        <img src="%s" title="%s" alt="%s"/>
                        <div class="desc">
                            <div class="titles">
                                <h3><a href="%s">%s</a></h3>
                                <p>%s</p>
                            </div>
                            <div class="proj_cat">
                                <h3>%s</h3>
                                <p>%s</p>
                            </div>
                        </div><!-- end desc -->
                    </li>
'''% (contentimages,contenttitle,contentexcerpt,contentlink,contenttitle,contentexcerpt[:50],contentauthorname,contentdate)

        content=content+contenthtml+'''
                </ul><!-- END UL FADER -->
                <div id="slide_desc">
                    <div class="titles">
                        <h3>Howdy! We are maxX Inc.</h3>
                        <p>This feature requires javascript. Kindly visit portfolio section to view images.</p>
                    </div>
                    <div class="proj_cat">
                        <h3>Hire Us</h3>
                        <p>WE'RE AVAILABLE</p>
                    </div>
                </div><!-- end slide desc -->
'''
        return content.encode('utf-8')

    def ipage(self,content,blog=None,*arg1,**arg2):
        contenthtml=''
        content= '''
                <ul id="fader">
               '''

        entries = Entry.all().filter('entrytype =','page').\
                filter("published =", True).order('-date').\
                filter("sticky =",True).\
                fetch(5)
        for entry in entries:
                if self.isphoto(entry.content)!=None:
                        logging.info(self.isphoto(entry.content))
                        contenttitle=entry.title
                        contentexcerpt=entry.excerpt
                        contentauthorname=entry.author_name
                        contentlink=entry.link
                        contentdate=str(entry.monthyear)
                        contentimages=str(self.isphoto(entry.content))
                        contenthtml+='''
                    <li>
                        <img src="%s" title="%s" alt="%s"/>
                        <div class="desc">
                            <div class="titles">
                                <h3><a href="%s">%s</a></h3>
                                <p>%s</p>
                            </div>
                            <div class="proj_cat">
                                <h3>%s</h3>
                                <p>%s</p>
                            </div>
                        </div><!-- end desc -->
                    </li>
'''% (contentimages,contenttitle,contentexcerpt,contentlink,contenttitle,contentexcerpt[:50],contentauthorname,contentdate)

        content=content+contenthtml+'''
                </ul><!-- END UL FADER -->
                <div id="slide_desc">
                    <div class="titles">
                        <h3>Howdy! We are maxX Inc.</h3>
                        <p>This feature requires javascript. Kindly visit portfolio section to view images.</p>
                    </div>
                    <div class="proj_cat">
                        <h3>Hire Us</h3>
                        <p>WE'RE AVAILABLE</p>
                    </div>
                </div><!-- end slide desc -->
'''
        return content.encode('utf-8')


    def isphoto(self,content):
            try:
                img=re.compile(r"""<img\s.*?\s?src\s*=\s*['|"]?([^\s'"]+).*?>""",re.I)
                m = img.findall(content)
                return m[0]
            except Exception,data:
                logging.info('the error is %s',data)
                return None



    def get(self,page):
        return '''<h3>PageSlider Plugin</h3>
               <p>PageSlider Plugin for CDM.</p>
               <p>This plugin based on CDM SYSTEM
                and cdm SYSTEM</p>
               <p><B>Please insert {%mf slider%}{%endmf%} to your wants pages</B>
'''
