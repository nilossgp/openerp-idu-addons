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
#
#    Creado por Andres Ignacio Baez Alba
#
##############################################################################

from openerp.osv import osv, fields
from openerp.osv.osv import except_osv
from lxml import etree
import xlrd
import base64
from tools.translate import _

class urban_bridge_wizard_import_elements(osv.osv_memory):
    """
    Wizard to load information from excel
    """ 
    _name="urban_bridge.wizard.import_elements"
    _columns={
        'bridge_id':fields.many2one('urban_bridge.bridge','Bridge'),
        'srid':fields.integer('Source SRID','Source Data System Reference'),
        'worksheet':fields.integer('Worksheet'),
        'element':fields.many2one('urban_bridge.structure_element_type','Element Type'),
        'file':fields.binary('File'),
    }
    #Va a la pagina 2 del wizard
    def next_1 (self,cr,uid,ids,context=None):
        search_obj = self.pool.get('ir.ui.view')
        search_id = search_obj.search(cr,uid,[('model','=','urban_bridge.wizard.import_elements'),\
                                              ('name','=','Import Elements - Select WorkSheet')])
        context["current_ids"]=ids[0]
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'urban_bridge.wizard.import_elements',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_id': search_id[0],
            'context': context
            }
    #Va a la página 3 del wizard
    def next_2 (self,cr,uid,ids,context=None):
        search_obj = self.pool.get('ir.ui.view')
        search_id = search_obj.search(cr,uid,[('model','=','urban_bridge.wizard.import_elements'),\
                                              ('name','=','Import Elements Select Fields')])
        context["current_ids"]=ids[0]
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'urban_bridge.wizard.import_elements',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'view_id': search_id[0],
            'context': context
            }
    
    
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        """
        Trae los campos de la vista para pintarla de manera adecuada
        
        """
        result = super(urban_bridge_wizard_import_elements, self).fields_view_get(cr, uid, view_id, \
                                        view_type, context, toolbar,submenu)
        search_obj = self.pool.get('ir.ui.view')
        #Se selecciona la hoja desde donde se van a importar los datos
       
        v_select_worksheet = search_obj.search(cr,uid,[('model','=','urban_bridge.wizard.import_elements'),\
                                              ('name','=','Import Elements - Select WorkSheet')])
        v_select_fields = search_obj.search(cr,uid,[('model','=','urban_bridge.wizard.import_elements'),\
                                              ('name','=','Import Elements Select Fields')])
        #Pagina 2 del Asistente -- arma combobox para seleccionar la hoja de cálculo
        if (view_id == v_select_worksheet[0]):
            current_id = context["current_ids"]
            wizard = self.browse(cr,uid,current_id,context=None)
            try :
                workbook = xlrd.open_workbook(file_contents=base64.decodestring(wizard.file))
                #wb = load_workbook(base64.decodestring(wizard.file))                
                worksheets = workbook.sheet_names()
                #worksheets = wb.get_sheet_names()
                x = 0
                combo_vals = []
                for worksheet_name in worksheets:
                    combo_vals.append(((str(x)+"_"+str(wizard.id)),str(worksheet_name)))
                    x = x+1
                result['fields']["cmb_worksheet"] = {
                        'domain':[],
                        'string':"Name",
                        'selectable':True,
                        'type':"selection",
                        'context':{},
                        'selection':combo_vals,
                        'required':True,
                        }
                xml=etree.fromstring(result['arch'])
                field = etree.Element("field",name="cmb_worksheet")
                xml.insert(1,field)
                result['arch'] = etree.tostring(xml)
            except Exception as e:
                raise except_osv(_('Error reading excel'), str(e))
                
        #Pagina 3 del Asistente -- arma el formulario que se despliega cuando se van a jalar los datos desde el excel
        elif (view_id == v_select_fields[0]):
            current_id = context["current_ids"]
            wizard = self.browse(cr,uid,current_id,context=None)
            #1. Armar un diccionario que va a funcionar en los comboboxes
            workbook = xlrd.open_workbook(file_contents=base64.decodestring(wizard.file))
            #worksheets = workbook.sheet_names()
            #if worksheets.__len__()>1:
            #    raise except_osv(_('File has more than one worksheet, please delete unused worksheets and try execute wizard again!'), str("Excel File error"))
            ws = workbook.sheets()[wizard.worksheet]
            x = 0
            combo_list = []
            #Columnas que se van a mostrar
            for col in range(ws.ncols):
                value = ws.cell(1,col).value
                combo_list.append((x,value))
                x=x+1
            #2. Determinar los campos que tienen el objeto y de acuerdo a los campos definidos en el objeto se crea una
            xml=etree.fromstring(result['arch'])
            maingroup = etree.Element("group",colspan="4",col="4")
            subgroup=etree.SubElement(maingroup,"group",colspan="4",col="2")
            etree.SubElement(subgroup, "separator", string=wizard.element.name)
            #3. El campo nombre que se encuentra en el objeto structure_element
            result['fields']["elem_name"] = {
                        'domain':[],
                        'string':"Name",
                        'selectable':True,
                        'type':"selection",
                        'context':{},
                        'selection':combo_list,
                        'required':True,
                        }
            etree.SubElement(maingroup,"field",name="elem_name")
            #4. El resto de atributos que se definen para el objeto. 
            for attribute in wizard.element.attributes:
                new_id = str(wizard.id)+"_"+str(wizard.element.id)+"_"+str(attribute.id)
                result['fields'][new_id] = {
                        'domain':[],
                        'string':attribute.name,
                        'selectable':True,
                        'type':"selection",
                        'context':{},
                        'selection':combo_list,
                        'required':True,
                        }
                etree.SubElement(maingroup,"field",name=new_id)
            xml.insert(1,maingroup)
            result['arch'] = etree.tostring(xml)
        return result
    
    
    def create(self, cr, uid, vals, context=None):
        """
        This method si called when every action at wizard
        """
        #0 El metodo se llama en cada pantallazo, en el primer pantallazo, se sube el fichero excel
        # en el segundo pantallazo, se recibe un diccionario donde indica como interpretar el excel para subir los valores y crearlos en la grilla
        if vals.has_key('elem_name'):
            try:
                #1. Determinar el wizard porque si no no es posible abrir el fichero de excel
                # como truco id del wizard esta dentro de la etiqueta dinámica de los campos
                id_wizard = 0
                for val in vals:
                    if not ((str(val) == 'elem_name') or (str(val) == 'bridge_id')):
                        id_wizard = int(val.split("_")[0])
                        break 
                # Objetos necesarios para hacer el cargue structure_element y value
                structure_element_obj=self.pool.get("urban_bridge.structure_element")
                wizard = self.browse(cr,uid,id_wizard,context=None)
                
                bridge = wizard.bridge_id
                #1. Abrir el fichero de excel
                
                workbook = xlrd.open_workbook(file_contents=base64.decodestring(wizard.file))
                ws = workbook.sheets()[wizard.worksheet]
                for row_index in range(ws.nrows):
                    #La fila 0 no tiene nada y la fila (1) tiene los títulos así que no nos interesa analizar
                    if row_index>1:
                        #Aca en adelante ojala se pudiera hacer una transaccion con rollback, investigar!!!
                        #2.Se debe crear el elemento con el nombre que venga en la clave elem_name y el el tipo de elemento que viene en el wizard
                        elem_name = ws.cell(row_index,int(vals['elem_name'])).value
                        elem_type = wizard.element
                        id_elem = None
                        # Se realiza búsqueda de elemento por nombre, si no existe ningun elemento de ese nombre entonces se procede a insertar
                        # si no se trata de una actualización 
                        for element in bridge.elements:
                            if (element.name == elem_name):
                                id_elem = element.id
                        if id_elem == None:
                                #Crear un elemento de infraestructura nuevo
                            id_elem=structure_element_obj.create (cr,uid,
                                                        {'bridge_id':bridge.id,
                                                        'element_type_id':elem_type.id,
                                                        'name':elem_name}
                                                        )
                        else :
                        #Se actualiza el puente que ya esta
                            structure_element_obj.write(cr,uid,id_elem,{
                                                                    'bridge_id':bridge.id,
                                                                    'element_type_id':elem_type.id,
                                                                    'name':elem_name
                                                                    })
                        #A cada elemento de infraestructura creado se le deben generar los atributos y valores
                        #Recorrer excel, armar diccionario e invocar metodo del wizard structure element.
                        element_values = {}
                        for att in elem_type.attributes:
                            #Se arma un diccionario de acuerdo al protocolo del metodo create del wizard structure_elemen.py
                            elem_key=str(elem_type.id)+"_"+str(att.id)+"_"+str(id_elem)
                            #El valor se saca del excel asumiendo que viene
                            #colocar aca un validador para que no vaya a generarse un error si algo pasa en esta línea de código
                            key_col = str(wizard.id)+"_"+str(elem_type.id)+"_"+str(att.id)
                            if vals.has_key(key_col):
                                col_index = int(vals[key_col])
                                #Algo pasa cuando el atributo es seleccion, si queda por ejemplo 2.0 despues no se despliega en el combobox, 
                                #es conveniente que al pasarlo a string no queden decimales.
                                elem_value =ws.cell(row_index,col_index).value
                                if (att.data_type=="selection"):
                                    try:
                                        #Aca el codigo es confuso y da una vuelta, la razón: el usuario puede definir en los comboboxes el tipo de 
                                        #atributo como le de la gana si define que el valor son strings por ejemplo [('a';'Amplio'),('v','vacio')]
                                        #Se generara un error al hacer una conversion %.0f porque va a entrar una v
                                        #Si el usuario define el diccionario [('1','Bueno'),('2','Malo')] cuando suba el fichero del excel va a encontrar
                                        #algo así en el valor 1.0, 2.0 3.0 y toca convertirlo a 1 2 por que si no, no va a aparecer el valor en los 
                                        #Combo Boxes.
                                        elem_f = float(elem_value)
                                        elem_value = str("%.0f" % elem_f)
                                    except Exception:
                                        #No hacer nada
                                        elem_value=str(elem_value)
                                element_values[elem_key]=elem_value
                        new_context=context
                        new_context["element_id"]=id_elem
                        new_context["element_type_id"]=elem_type.id
                        wizard_structure_elem_obj=self.pool.get("urban_bridge.wizard.structure_elem")
                        wizard_structure_elem_obj.create(cr,uid,element_values,new_context)
                return wizard.id
            except Exception :
                raise except_osv(_('Wizard Load Fail'), str("field error"))
        #Este if entra luego de que se pulsa next en el segundo pantallazo del wizard cuando escoje la hoja de trabajo
        elif vals.has_key('cmb_worksheet'):
            id_wizard = int(vals['cmb_worksheet'].split("_")[1])
            worksheet_index = int(vals['cmb_worksheet'].split("_")[0])
            wizard = self.pool.get("urban_bridge.wizard.import_elements")
            wizard.write(cr,uid,id_wizard,{'worksheet':worksheet_index})
            return id_wizard
        else: 
            id_val = super(urban_bridge_wizard_import_elements,self).create(cr, uid, vals, context=context)
            return id_val
        
        
    def default_get(self,cr, uid, fields, context=None):
        """
        Fields View Get method :- generate the new view and display the survey pages of selected survey.
        """
        spatial_ref_sys = self.pool.get('ir.config_parameter').get_param(cr, uid, 'urban_bridge.local_spatial_reference', default='', context=context)
        res = super(urban_bridge_wizard_import_elements, self).default_get(cr, uid, fields, context=context)
        res['bridge_id']=context['active_id']
        res['srid']=int(spatial_ref_sys)
        return res


    def import_elements(self,cr,uid,ids,context=None):
        """
        Import
        """
        res = {'type': 'ir.actions.act_window_close'}
        return res
    
    
    
    
urban_bridge_wizard_import_elements()

    
