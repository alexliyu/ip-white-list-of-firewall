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
import re
import logging
"""
DOM选择器,支持以CSS选择器的方式来获得所需的DOM片段.

本模块的的功能实现主要依赖于第三方库BeautifulSoup.
"""

# ================================ utils funtions ================================

def tokenize(target):
    """
    把用户输入的CSS选择器风格的表达式分解成Token,以空格为界.
    """
    if target:
        tokens = target.split(' ')
        for token in tokens:
            if token:
                yield token
            else:
                continue

def checkTokenType(token):
    """
    检测Token的类型.类型分为类,ID,标签以及操作符(如,>,+)
    """
    d = {'.':'class','#':'id','+':'op','>':'op'}
    if token[0] in d:
        return d[token[0]]
    else:
        return 'tag'

def findByAttr(d,html,recursive=True,findnext=False):
    """
    根据指定属性找到符合条件的DOM片段.
    """
    if findnext:
        return html.findNextSiblings(attrs=d)
    else:
        return html.findAll(attrs=d,recursive=recursive)
#    print html.findAll(attrs={"class" : re.compile("bct*")})
#    return html.findAll(attrs={"class" : re.compile("pb_box_lrad2_show*")})
def findById(id,html,recursive=True,findnext=False):
    """
    根据指定的ID查找符合条件的DOM片段.
    """
    return findByAttr({'id':id[1:len(id)]}, html)

def findByClass(cls,html,recursive=True,findnext=False):
    """
    根据指定的类命查找符合条件的DOM片段.
    """
#    print {'class':cls[1:len(cls)]}
    tempstr=cls[1:len(cls)]+'*'
    #logging.info(html)
    return findByAttr({'class':re.compile(tempstr)},html)

def findByTag(tag,html,recursive=True,findnext=False):
    """
    根据指定的Tag查找符合条件的DOM片段.Tag除了包含标签名,还可能含有ID,类信息以及其他属性值.如:
    DIV.item#theone[style=my] .
    上面是一个完整的标签片段示例.
    参数解释:
    tag: 标签字符串,可附带类,ID,属性信息.
    html: 必须是BeautifulSoup实例或Tag实例.
    recurisive: 是否遍历所有子结点?
    findnext:是否查找相邻结点,False则查找子结点.
    """

    # 非标签名的特殊字符
    special_chars = ['.','#','[',']']

    # 先找到标签名.
    tagname = ''
    for c in tag:
        if c in special_chars:
            # 一出现有其它字符则标识Tag名读取完成了.
            break
        else:
            tagname += c

    # 再找到所有的属性
    attrs = {}
    attrs_str = tag[len(tagname):len(tag)]

    if '[' in attrs_str:
        # 其他属性
        ats = attrs_str[attrs_str.index('['):attrs_str.rindex(']') + 1]
        attr_group = ats[1:len(ats) - 1].split(',')
        for attr in attr_group:
            tmp = attr.split('=')
            attrs[tmp[0]] = tmp[1]

        attrs_str = attrs_str.replace(ats,'') # 删掉其他属性部分字符串.

    # 将ID,Class转为属性值.
    name = ''
    value = ''
    for c in attrs_str:
        if c == '.':
            if name : attrs[name] = value
            name = 'class'
            value = ''
        elif c == '#':
            if name : attrs[name] = value
            name = 'id'
            value = ''
        else:
            if name:
                value += c

    # 不能忘了还有一个值捏...
    if value:
        attrs[name] = value
    if findnext:
        return html.findNextSiblings(tagname,attrs=attrs)
    else:
        return html.findAll(tagname,attrs,recursive=recursive)



handlers = {'tag':findByTag,'id':findById,'class':findByClass}

def findAll(target,soup):
    """
    在HTML中找到所有符合条件的结果并返回.
    target:目标位置表达式
    soup:BeautifulSoup的实例,选择器将从这碗汤里获得目标

    实现流程:
    拆分位置表达式为Token集,以空格为分界.空格是默认的操作符.如".my div"的空格意思是class=my标签内部的所有div(子甚至孙)都有效.
    遍历token,如果token是操作符(+,>)则设置标识,告知下一个Token要进行非空格的操作.如果遇到是非操作符的token则交给相应的处理器去处理.
    每一个token处理的结果将会被作为下一个token的输入.
    最终返回所以符合条件的DOM片段.
    """
    pre_datas = []
    recursive=True
    findnext=False
    for token in tokenize(target):
        if token:
            kind = checkTokenType(token)
            # 获得当前token的类型,交给不同的处理器处理,处理返回结果是一个列表.遍历列表,将每个结果交由下一个Token处理.
            #这里需要上一次的结果
            if kind == 'op':
                # 如果是操作符,则设置标识参数,然后继续下一个标签.
                if token == '>' : recursive = False
                elif token == '+' : findnext = True
                continue

            if pre_datas:
                new_data = []
                for data in pre_datas:
                    # 将上一个token的每一个处理结果作为本Token的输入,得到的结果作为下一个Token的输入.
                    new_data += handlers[kind](token,data,recursive,findnext)
                pre_datas = new_data
            else:
                pre_datas += handlers[kind](token,soup)

        # 每一个Token解释完后复位一下两个标识,等遇到下一个操作符再去修改.
        recursive=True
        findnext=False
    return pre_datas
