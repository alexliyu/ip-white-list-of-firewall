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
# Django settings for the example project.
import os

DEBUG = True
TEMPLATE_DEBUG = False

LANGUAGE_CODE = 'zh-CN'
##LANGUAGE_CODE = 'fr'
LOCALE_PATHS = 'locale'
USE_I18N = True

TEMPLATE_LOADERS=('django.template.loaders.filesystem.load_template_source',
                    'ziploader.zip_loader.load_template_source')

