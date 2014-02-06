# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2013 Instituto de Desarrollo Urbano (<http://www.idu.gov.co>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv

class plan_contratacion_idu_plan(osv.osv):
    _name = "plan_contratacion_idu.plan"


    def _get_currency(self, cr, uid, ids, field, args, context=None):
        res = {}
        company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'plan_contratacion_idu.plan', context=context)
        company = self.pool.get('res.company').read(cr, uid, company_id, ['currency_id'])
        currency_id = company['currency_id'][0]
        for plan_id in ids:
            res[plan_id] = currency_id
        return res

    def _total_pagos_plan(self, cr, uid, ids, name, args, context=None):
        res = {}
        if isinstance(ids, (list, tuple)) and not len(ids):
            return res
        if isinstance(ids, (long, int)):
            ids = [ids]
        records = self.browse(cr, uid, ids, context=context)
        res = {}
        for record in records:
            sumatoria = 0
            sumatoria_presupuesto = 0
            res[record['id']] = {}
            for pago in record.item_ids:
                sumatoria += pago.total_pagos_programados
                sumatoria_presupuesto += pago.presupuesto
            res[record['id']]['total_pagos_presupuestado_plan'] = sumatoria_presupuesto
            res[record['id']]['total_pagos_programados_plan'] = sumatoria
            res[record['id']]['total_rezago_plan'] = sumatoria_presupuesto - sumatoria
        return res

    _columns = {
        'name': fields.char('Vigencia', size=255, required=True, select=True),
        'state':fields.selection([('draft', 'Draft'),('open', 'In Progress'),('cancel', 'Cancelled'),('done', 'Done'),('pending', 'Pending')],'State', required=True),
        'active':fields.boolean('Activo'),
        'item_ids': fields.one2many('plan_contratacion_idu.item', 'plan_id', 'Items Plan de Contratacion'),
        'name_items':fields.one2many('plan_contratacion_idu.item', 'name', 'Items Plan de Contratacion'),
        'currency_id': fields.function(_get_currency, type='many2one', relation="res.currency", method=True, string='Currency', readonly=True),
        'total_pagos_presupuestado_plan': fields.function(_total_pagos_plan, type='float', multi="total_pagos_programados", string='Total Presupuestado', digits_compute=dp.get_precision('Account'), readonly = True,
             store={
             }),
        'total_pagos_programados_plan': fields.function(_total_pagos_plan, type='float', multi="total_pagos_programados", string='Total Pagos Programados', digits_compute=dp.get_precision('Account'),
             store={
             }),
        'total_rezago_plan': fields.function(_total_pagos_plan, type='float', multi="total_pagos_programados", string='Total Rezago', digits_compute=dp.get_precision('Account'),
             store={
             }),
    }
    _sql_constraints =[
        ('unique_name','unique(name)','El año del plan debe ser único')
    ]
     
    _defaults = {
        'active': True,
        'state': 'draft'
    }

plan_contratacion_idu_plan()

class plan_contratacion_idu_item(osv.osv):
    _name = "plan_contratacion_idu.item"
    _inherit = ['mail.thread']

    _track = {
        'state': {
            'plan_contratacion_idu.item_draft': lambda self, cr, uid, obj, ctx=None: obj['state'] in ['draft'],
            'plan_contratacion_idu.item_estudios_previos': lambda self, cr, uid, obj, ctx=None: obj['state'] in ['estudios_previos', 'ejecucion'],
            'plan_contratacion_idu.item_radicado': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'radicado',
            'plan_contratacion_idu.item_suscrito': lambda self, cr, uid, obj, ctx=None: obj['state'] == 'suscrito',
        },
    }
 
    def _total_pagos_programados(self, cr, uid, ids, name, args, context=None):
        res = {}
        if isinstance(ids, (list, tuple)) and not len(ids):
            return res
        if isinstance(ids, (long, int)):
            ids = [ids]
        records = self.browse(cr, uid, ids, context=context)
        res = {}
        for record in records:
            sumatoria = 0
            res[record['id']] = {}
            for pago in record.plan_pagos_item_ids:
                sumatoria += pago.valor
            res[record['id']]['total_pagos_programados'] = sumatoria
            res[record['id']]['presupuesto_rezago'] = record.presupuesto - sumatoria
            res[record['id']]['total_programado_rezago'] = sumatoria + (record.presupuesto - sumatoria)
        return res

    def _get_plan_item_from_pago_records(self, cr, uid, pago_ids, context=None):
        """
        Retorna los IDs del plan_item a ser recalculados cuando cambia un pago_item
        """
        pago_records = self.pool.get('plan_contratacion_idu.plan_pagos_item').browse(cr, uid, pago_ids, context=context)
        plan_item_ids = [pago.plan_contratacion_item_id.id for pago in pago_records if pago.plan_contratacion_item_id]
        return plan_item_ids

    def _check_fechas_programadas(self,cr,uid,ids,context=None):
        """valida las fechas programadas"""
        res = {}
        if isinstance(ids, (list, tuple)) and not len(ids):
            return res
        if isinstance(ids, (long, int)):
            ids = [ids]
        records = self.browse(cr, uid, ids, context=context)
        res = {}
        for record in records:
            if record.fecha_crp >= record.fecha_radicacion and record.fecha_acta_inicio >= record.fecha_crp:
                return True
            else:
                return False

    def _check_state(self,cr,uid,ids,context=None):
        """valida el cambio de estado"""
        res = {}
        if isinstance(ids, (list, tuple)) and not len(ids):
            return res
        if isinstance(ids, (long, int)):
            ids = [ids]
        records = self.browse(cr, uid, ids, context=context)
        res = {}
        for record in records:
            if record.state == 'draft':
                return True
            if record.state == 'estudios_previos':
                return True
            if record.state=='ejecucion':
                if record.acta_inicio:
                    return True
                else:
                    return False
            if record.state == 'ejecutado':
                if record.acta_liquidacion:
                    return True
                else:
                    return False

    def _check_state_radicado(self,cr,uid,ids,context=None):
        """valida el cambio de estado"""
        res = {}
        if isinstance(ids, (list, tuple)) and not len(ids):
            return res
        if isinstance(ids, (long, int)):
            ids = [ids]
        records = self.browse(cr, uid, ids, context=context)
        res = {}
        is_valid = True
        for record in records:
            if record.state == 'radicado':
                if record.numero_orfeo:
                    is_valid = True
                else:
                    is_valid = False
        return is_valid

    def _check_state_suscrito(self,cr,uid,ids,context=None):
        """valida el cambio de estado"""
        res = {}
        if isinstance(ids, (list, tuple)) and not len(ids):
            return res
        if isinstance(ids, (long, int)):
            ids = [ids]
        records = self.browse(cr, uid, ids, context=context)
        res = {}
        is_valid = True
        for record in records:
            if record.state == 'suscrito':
                if record.numero_crp:
                    is_valid = True
                else:
                    is_valid = False
        return is_valid

    def _check_state_ejecucion(self,cr,uid,ids,context=None):
        """valida el cambio de estado """
        res = {}
        if isinstance(ids, (list, tuple)) and not len(ids):
            return res
        if isinstance(ids, (long, int)):
            ids = [ids]
        records = self.browse(cr, uid, ids, context=context)
        res = {}
        is_valid = True
        for record in records:
            if record.state == 'ejecucion':
                if record.numero_crp:
                    is_valid = True
                else:
                    is_valid = False
        return is_valid

    def _check_state_ejecutado(self,cr,uid,ids,context=None):
        """valida el cambio de estado"""
        res = {}
        if isinstance(ids, (list, tuple)) and not len(ids):
            return res
        if isinstance(ids, (long, int)):
            ids = [ids]
        records = self.browse(cr, uid, ids, context=context)
        res = {}
        is_valid = True
        for record in records:
            if record.state == 'ejecutado':
                if record.numero_crp:
                    is_valid = True
                else:
                    is_valid = False
        return is_valid

    _columns = {
        'dependencia': fields.many2one('hr.department','Dependencia', select=True, ondelete='cascade'),
        'description': fields.text('Objeto Contractual', states={'suscrito':[('readonly',True)], 'ejecucion':[('readonly',True)], 'ejecutado':[('readonly',True)]}),
        'name': fields.many2one('plan_contratacion_idu.plan','Plan contractual', select=True, ondelete='cascade'),
        'centro_costo': fields.char('Centro de Costo', size=255),
        'nombre_proyecto_idu':fields.char('Nombre Proyecto IDU', size=255, domain="[('parent_id','=',centro_costo),('enabled','=',False)]",),
        'nombre_punto_inversion':fields.char('Nombre Punto de Inversión', size=255),
        'fuente': fields.many2one('plan_contratacion_idu.fuente','Fuente de Financiación', select=True, ondelete='cascade'),
        'state':fields.selection([('draft', 'Draft'),('estudios_previos', 'Estudios Previos'),('radicado', 'Radicado'),('suscrito', 'Contrato Suscrito'),('ejecucion', 'En ejecución'),
                                  ('ejecutado', 'Ejecutado'), ('no_realizado', 'No realizado')],'State',
                                  track_visibility='onchange', required=True),
        'fecha_radicacion': fields.date ('Fecha Radicacion en DTPS y/o DTGC', state={'draft':[('required',False)],'estudios_previos':[('required',False)]}, required=True, select=True),
        'fecha_crp': fields.date ('Fecha Programada CRP', state={'draft':[('required',False)],'estudios_previos':[('required',False)]}, required=True, select=False, help="CRP es Certificado Registro Presupuestal"),
        'fecha_acta_inicio': fields.date ('Fecha Aprobación Acta de Inicio', state={'draft':[('required',False)],'estudios_previos':[('required',False)]}, required=True, select=True),
        'plan_id': fields.many2one('plan_contratacion_idu.plan','Plan contractual', select=True, ondelete='cascade'),
        'clasificacion_id': fields.many2one('plan_contratacion_idu.clasificador_proyectos','Clasificación Proyecto', select=True, ondelete='cascade'),
        'presupuesto': fields.float ('Presupuesto', required=True, select=True, obj="res.currency", track_visibility='onchange'),
        'plazo_de_ejecucion': fields.char('Plazo de Ejecución', required=True, select=True, help="Tiempo estimado en meses"),
        'unidad_meta_fisica': fields.char('Unidad Meta Física', size=255),
        'cantidad_meta_fisica': fields.char ('Cantidad Metas Físicas', size=255),
        'localidad': fields.char ('Localidad', size=255),
        'currency_id': fields.related('plan_id','currency_id',type='many2one',relation='res.currency',string='Company',store=True, readonly=True),
        'tipo_proceso': fields.many2one('plan_contratacion_idu.plan_tipo_proceso_item','Tipo Proceso', select=True, ondelete='cascade'),
        'tipo_proceso_seleccion': fields.many2one('plan_contratacion_idu.plan_tipo_proceso_seleccion_item','Tipo Proceso de Selección', select=True, ondelete='cascade'),
        'plan_pagos_item_ids': fields.one2many('plan_contratacion_idu.plan_pagos_item','plan_contratacion_item_id', 'Planificacion de Pagos', select=True, ondelete='cascade'),
        'total_pagos_programados': fields.function(_total_pagos_programados, type='float', multi="presupuesto", string='Total pagos programados', obj="res.currency", digits_compute=dp.get_precision('Account'),
             store={
                'plan_contratacion_idu.item': (lambda self, cr, uid, ids, c={}: ids, ['plan_pagos_item_ids', 'presupuesto'], 10),
                'plan_contratacion_idu.plan_pagos_item': (_get_plan_item_from_pago_records, ['valor', 'plan_contratacion_item_id'], 20),
            }),
        'presupuesto_rezago': fields.function(_total_pagos_programados, type='float', multi="presupuesto", string='Rezago', obj="res.currency", digits_compute=dp.get_precision('Account'),
             store={
                'plan_contratacion_idu.item': (lambda self, cr, uid, ids, c={}: ids, ['plan_pagos_item_ids', 'presupuesto'], 10),
                'plan_contratacion_idu.item': (lambda self, cr, uid, ids, c={}: ids, ['presupuesto', 'presupuesto'], 10),
                'plan_contratacion_idu.plan_pagos_item': (_get_plan_item_from_pago_records, ['valor', 'plan_contratacion_item_id'], 20),
            }),
        'total_programado_rezago': fields.function(_total_pagos_programados, type='float', multi="presupuesto", string='Total', obj="res.currency", digits_compute=dp.get_precision('Account'),
             store={
                'plan_contratacion_idu.item': (lambda self, cr, uid, ids, c={}: ids, ['plan_pagos_item_ids', 'presupuesto'], 10),
                'plan_contratacion_idu.item': (lambda self, cr, uid, ids, c={}: ids, ['presupuesto', 'presupuesto'], 10),
                'plan_contratacion_idu.plan_pagos_item': (_get_plan_item_from_pago_records, ['valor', 'plan_contratacion_item_id'], 20),
            }),
        'numero_orfeo':fields.char('Número Radicado Orfeo', help='Validado desdes Orfeo', states={'estudios_previos':[('readonly',False)]}, readonly=True,
                                   track_visibility='onchange'),
        'numero_crp':fields.char('Numero CRP', help ='Validado desde Stone', states={'radicado':[('readonly',False)]}, readonly=True,
                                 track_visibility='onchange'),
        'numero_contrato': fields.char('Numero Contrato', help ='Validado desde SIAC', states={'suscrito':[('readonly',False)]}, readonly=True,
                                       track_visibility='onchange'),
        'acta_inicio':fields.date('Fecha acta de inicio', help = 'Validador desde SIAC', readonly=True),
        'acta_liquidacion':fields.date('Fecha acta de Liquidacion', help = 'Validador desde SIAC',readonly =True),
    }

    _defaults = {
        'state': 'draft'
    }

    _constraints = [(_check_fechas_programadas,
                    "La fecha programada CRP debe ser posterior a la fecha programada de radicación y anterior a la fecha programada para la aprobación del acta de Inicio",
                    ['fecha_crp','fecha_acta_inicio']),
                    (_check_state_radicado,
                    "Para cambiar el estado a Radicado debe ingresar el número de radicado Orfeo en información de verificación",
                    ['state']),
                    (_check_state_suscrito,
                    "Para cambiar el estado a Contrato Suscrito debe ingresar el número CRP en información de verificación",
                    ['state']),
                    (_check_state_ejecucion,
                    "Para cambiar el estado a Ejecucion debe ingresar el número del contrato en información de verificación",
                    ['state']),
                    (_check_state_ejecutado,
                    "Para cambiar el estado a Ejecutado debe ingresar el número del contrato en información de verificación",
                    ['state']),
                    ]

    def onchange_plan_pagos_item_ids(self, cr, uid, ids, pagos_ids, context=None):
        context = context or {}
        pagos_pool = self.pool.get('plan_contratacion_idu.plan_pagos_item')
        if not pagos_ids:
            pagos_ids = []
        sumatoria = 0
        res = {
                'total_pagos_programados': 0,
                'presupuesto_rezago': 0,
        }
        pagos_ids = resolve_o2m_operations(cr, uid, pagos_pool, pagos_ids, ['valor'], context)
        if ids:
            plan_item = self.read(cr, uid, ids[0], ['presupuesto'], context=context)
            for pago in pagos_ids:
                sumatoria += pago.get('valor',0.0)
            res = {
                'total_pagos_programados': sumatoria,
                'presupuesto_rezago': plan_item['presupuesto'] - sumatoria,
                'total_programado_rezago': sumatoria + (plan_item['presupuesto'] - sumatoria),
            }
        return {
            'value': res
        }

    def action_invoice_sent(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi invoice template message loaded by default
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        ir_model_data = self.pool.get('ir.model.data')
        try:
            template_id = ir_model_data.get_object_reference(cr, uid, 'account', 'email_template_edi_invoice')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'plan_contratacion_idu.item',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_invoice_as_sent': True,
            })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def wkf_draft(self, cr, uid, ids, plan_items, context=None):
        self.write(cr, uid, ids, {"state": "draft"})

    def wkf_estudios_previos(self, cr, uid, ids, plan_items, context=None):
        self.write(cr, uid, ids, {"state": "estudios_previos","numero_orfeo":"",
                                  "numero_crp":"", "numero_contrato":None})

    def wkf_radicado(self, cr, uid, ids, plan_items, context=None):
        self.write(cr, uid, ids, {"state": "radicado"})

    def wkf_no_realizado(self, cr, uid, ids, plan_items, context=None):
        self.write(cr, uid, ids, {"state": "no_realizado"})
    
    def wkf_suscrito(self, cr, uid, ids, plan_items, context=None):
        self.write(cr, uid, ids, {"state": "suscrito"})

    def wkf_ejecucion(self, cr, uid, ids, plan_items, context=None):
        self.write(cr, uid, ids, {"state": "ejecucion"})

    def wkf_ejecutado(self, cr, uid, ids, plan_items, context=None):
        self.write(cr, uid, ids, {"state": "ejecutado"})

plan_contratacion_idu_item()

class plan_contratacion_idu_clasificador_proyectos(osv.osv):
    _name = "plan_contratacion_idu.clasificador_proyectos"
    _description = "Clasificación de los proyectos"
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'sequence, name'
    _order = 'parent_right DESC'

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name','parent_id'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['parent_id']:
                name = record['parent_id'][1]+' / '+name
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _columns = {
        'codigo': fields.integer ('Código', required=True, select=True),
        'name': fields.char('Nombre', size=255, required=True, select=True),
        'tipo': fields.selection([('proyecto_inversion', 'Proyecto de Inversión'),('proyecto_prioritario', 'Proyecto Prioritario')],'Tipo', required=True),
        'complete_name': fields.function(_name_get_fnc, type="char", string='Nombre'),
        'parent_id': fields.many2one('plan_contratacion_idu.clasificador_proyectos','Clasificación padre', select=True, ondelete='cascade'),
        'child_ids': fields.one2many('plan_contratacion_idu.clasificador_proyectos', 'parent_id', string='Clasificaciones hijas'),
        'sequence': fields.integer('Sequence', select=True, help="Secuencia para el ordenamiento en las listas"),
        'parent_left': fields.integer('Left Parent', select=1),
        'parent_right': fields.integer('Right Parent', select=1),
        'active':fields.boolean('Active',help='Activo/Inactivo'),
        'item_ids': fields.one2many('plan_contratacion_idu.item', 'clasificacion_id', 'Items Plan de Contratacion'),
    }

    _defaults = {
        'active': True,
    }

    def _check_recursion(self, cr, uid, ids, context=None):
        level = 100
        while len(ids):
            cr.execute('select distinct parent_id from plan_contratacion_idu_clasificador_proyectos where id IN %s',(tuple(ids),))
            ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            if not level:
                return False
            level -= 1
        return True
    _constraints = [
        (_check_recursion, 'Error ! No puede crear clasificaciones recursivas.', ['parent_id']),
    ]

plan_contratacion_idu_clasificador_proyectos()

class plan_contratacion_idu_fuente(osv.osv):
    _name = "plan_contratacion_idu.fuente"
    _columns = {
        'codigo_fuente':fields.char('Codigo Fuente',size=10,required=True, select=True),
        'name': fields.char('Nombre', size=50, required=True, select=True),
        'codigo_fuente_sdh': fields.char('Codigo Fuente Secretaria Distrital de Hacienda',size=10,required=True, select=True),
        'nombre_fuente_sdh': fields.char('Nombre Fuente Secretaria Distrital de Hacienda', size=50, required=True, select=True),
        'codigo_detalle_fuente_sdh': fields.char('Código detalle fuente Secretaria Distrital de Hacienda',size=10, required=True, select=True),
        'nombre_detalle_fuente_sdh': fields.char('Nombre detalle fuente Secretaria Distrital de Hacienda',size=50, select=True),
    }
plan_contratacion_idu_fuente()

class plan_contratacion_idu_plan_pagos_item(osv.osv):
    _name = "plan_contratacion_idu.plan_pagos_item"
    _columns = {
        'mes': fields.selection([(1,'Enero'), (2,'Febrero'), (3,'Marzo'), (4,'Abril'),
            (5,'Mayo'), (6,'Junio'), (7,'Julio'), (8,'Agosto'), (9,'Septiembre'),
            (10,'Octubre'), (11,'Noviembre'), (12,'Diciembre')], 'Mes', required=True),
        'valor': fields.float('Valor', required=True, select=True, obj="res.currency"),
        'plan_contratacion_item_id': fields.many2one('plan_contratacion_idu.item','Item Plan de Contratacion', select=True, ondelete='cascade'),
        'currency_id': fields.related('plan_contratacion_item_id','currency_id',type='many2one',relation='res.currency',string='Company',store=True,readonly=True),
    }

    _sql_constraints =[
        ('unique_mes','unique(mes,plan_contratacion_item_id)','El mes debe ser único')
    ]

    _order = 'mes'

plan_contratacion_idu_plan_pagos_item()

class plan_contratacion_idu_plan_tipo_proceso_item(osv.osv):
    _name = "plan_contratacion_idu.plan_tipo_proceso_item"
    _columns = {
        'name':fields.char('Nombre', size=255, required=True, select=True),
    }

    _sql_constraints =[
        ('unique_name','unique(name)','El tipo de proceso debe ser único')
    ]

plan_contratacion_idu_plan_tipo_proceso_item()

class plan_contratacion_idu_plan_tipo_proceso_seleccion_item(osv.osv):
    _name = "plan_contratacion_idu.plan_tipo_proceso_seleccion_item"
    _columns = {
        'name':fields.char('Nombre', size=255, required=True, select=True),
    }

    _sql_constraints =[
        ('unique_name','unique(name)','El tipo de proceso debe ser único')
    ]

def resolve_o2m_operations(cr, uid, target_osv, operations, fields, context):
    results = []
    for operation in operations:
        result = None
        if not isinstance(operation, (list, tuple)):
            result = target_osv.read(cr, uid, operation, fields, context=context)
        elif operation[0] == 0:
            # may be necessary to check if all the fields are here and get the default values?
            result = operation[2]
        elif operation[0] == 1:
            result = target_osv.read(cr, uid, operation[1], fields, context=context)
            if not result: result = {}
            result.update(operation[2])
        elif operation[0] == 4:
            result = target_osv.read(cr, uid, operation[1], fields, context=context)
        if result != None:
            results.append(result)
    return results

