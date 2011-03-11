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
import re
import logging
class GetNewUrl():
		def Geturl(self,oldurl,*args):
				#kwargs=[]
				#newurl=''
				#logging.info(oldurl)
				#btype=re.findall('[^/]\w+',oldurl)
				btype=re.findall('[^/]\w*',oldurl)
				##kwargs=self.Check_kwargs(btype)
				#
				#
				#newurl=self.Check_Url(btype,*args)
				#if newurl:
				#		return newurl
				#else:
				#		return None
				return btype

		def Make_Page(self,oldurl,value=None,index=False):
				url=''
				newurl=''
				c=0
				logging.info(oldurl)
				if oldurl=='/' and index==True:oldurl+='blog/'
				if oldurl.find('/page/')!=-1:
						if oldurl[-1]!='/' and oldurl[-1].isdigit():
								newurl=oldurl.rsplit('/page/',1)[0]+'/page/%s'
						else:
								newurl=oldurl+'%s'
				else:
						if oldurl[-1]!='/':
								newurl=oldurl+'/page/%s'
						else:
								newurl=oldurl+'page/%s'
				return newurl% str(value)
#TODO like /blog/?page=2 or /blog/?p=23 or blog/?page=1
		def Check_Url(self,url,*args):
				newurl=''
				tmpurl=''
				kwargs=dict()
				x=0
				temp=url[:-1][0]
				if len(url)>=3:
						kwargs=dict(count=len(url))

						for i in url:
							if i[:1]=='?':
								x=url.index(i)
							kwargs.update({self.Make_tag(url.index(i)):i})
						if x==0 and type(url[:-2]) == int:
							tmpurl=''.join(url[:-1])
						else:
							tmpurl=''.join(url[:-2])
						kwargs.update(type=tmpurl)

				else:
						tmpurl=''.join(url)

				urltype= dict((['blog?page', 'blogpage'],['blog?p' ,'blogp'],\
						['blogcategory','blogcategorypage'],\
						['blogcategory?page','blogcategorypage'],\
						['archive','archivepage']))
				#if len(kwargs)>0:
				#				tmpurl=tmpurl.replace(kwargs['a1'],'#int')
				#				tmpurl=tmpurl.replace(kwargs['a2'],'#int')


				if urltype[tmpurl]:
						newurl=self.Make_url(urltype[tmpurl],*args,**kwargs)
				else:
						newurl=None
				return newurl
		def Make_tag(self,i):
				return '#a'+str(i+1)

		def Make_url(self,order=None,*args,**kwargs):
				ordertype=dict((['blogpage', '/blog/%s/?page=%s'],\
						['albumtag','/album/tag/%s'],\
						['tag','/tag/%s'],\
						['category','/%s/category/%s'],\
						['archive','/archive/%s/%s'],\
						['entrylink','/%s/%s'],\
						['editentry','/admin/%s?type=%s&key=%s&action=edit'],\
						['trackbackurlo','/%s%s&code=%s'],\
						['trackbackurlt','/%s%s?code=%s'],\
						['albumcover','http://%s/sserve/?w=200&p=%s'],\
						['albumcovera','http://%s/sserve/?w=s&p=%s'],\
						['albumcoverb','http://%s/serve/?%s'],\
						['albumurl','http://%s/alubm/%s.html'],\
						['albumlink','%s/%s.html'],\
						['albumeditlink','/admin/albums/edit/%s/?keepThis=true'],\
						['photolink','http://%s/serve/?%s.jpg'],\
						['photolinks','http://%s/sserve/?w=s&p=%s.jpg'],\
						['photolinkc','http://%s/sserve/?w=100&p=%s.jpg'],\
						['photolinkg','http://%s/sserve/?w=g&p=%s.jpg'],\
						['photolinkurlo','%s/photo/%s'],\
						['photolinkurlt','%s/photo/?u=%s'],\
						['photolinkedit','/admin/photo/?edit=%s&album=%s'],\
						['cookurl','comment_user=%s;expires=%s;domain=%s;path=/'],\
						['entrycommurlo','/%s&mp=%s#comments'],\
						['entrycommurlt','/%s?mp=%s#comments'],\
						['gallerylink','/gallery/%s.html'],\
						['archivepage','/archive/#a1#a2?p=%s']))

				orderlist=args
				#logging.info(order)
				newurl=ordertype[order]
				#logging.info(newurl)
				if len(kwargs)>0:
						for i in kwargs:
							#logging.info(unicode(kwargs[i]))
							newvalue=unicode(kwargs[i])+'/'
							#logging.info(newvalue)
							#logging.info(i)
							newurl=newurl.replace(i,newvalue)

				else:
						p=re.compile('(#a[0-9])+')
						p.sub('',newurl)

				#logging.info(newurl)
				if len(orderlist)>0:
						newurl=newurl% orderlist
				if newurl[-1]=='/':
						newurl=newurl[0:-1]
				if newurl:
					return newurl
				else:
					return None

		def Make_newurl(self,order,*args):

				kwargs=self.Make_value(*args)
				#logging.info(kwargs)
				result=self.Make_url(order,**kwargs)
				if result:
						return result
				else:
						return None

		def Make_adminurl(self,order,*args):
				result=self.Make_url(order,*args)
				if result:
						return result
				else:
						return None

		def Make_value(self,*args):
				kwargs=dict()
				for i in args:
						kwargs.update({self.Make_tag(args.index(i)):i})
				return kwargs
