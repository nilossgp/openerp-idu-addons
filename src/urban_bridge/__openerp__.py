# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# Generated by the OpenERP plugin for Dia !
{
        "name" : "Bridge Management System",
        "version" : "0.1",
        "author" : "Angel María Fonseca, Andres Ignacio Baez Alba and Cinxgler Mariaca Minda",
        "website" : "www.idu.gov.co",
        "category" : "Transportation, Free Bridge Management System",
        "description": """For Public Organizations, this is a bridge management System, first module Bridge inventory survey.""",
        "depends" : ['base',
                     'base_map',
                     ],
        "init_xml" : ['urban_bridge_view.xml'],
        "demo_xml" : [],
        "update_xml" : ['urban_bridge_view.xml',
                        ],
        "installable": True
}
