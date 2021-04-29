# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime


class HSSalesProvince(models.Model):
    _name = 'hs.sales.province'
    _rec_name = 'name'
    _description = '省'

    name = fields.Char(string='名称')
    province_number = fields.Char(string='编码')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Province name already exists!'),
    ]


class HSSalesCity(models.Model):
    _name = 'hs.sales.city'
    _rec_name = 'name'
    _description = '市'

    name = fields.Char(string='名称')
    city_number = fields.Char(string='编码')
    province_number = fields.Char(string='省编码')
    province_id = fields.Many2one('hs.sales.province', string='省')
    complete_name = fields.Char(compute='_compute_complete_name')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'City name already exists!'),
    ]

    @api.one
    @api.depends('province_id')
    def _compute_complete_name(self):
        self.complete_name = self.province_id.name + ' ' + self.name


class BatchDealProvinceWizard(models.TransientModel):
    _name = 'hs.sales.batch.deal.province.wizard'
    _description = 'Batch wizard'

    city_ids = fields.Many2many(comodel_name='hs.sales.city',
                                relation="hs_sales_notes_batch_deal_prov_wizard_rel",
                                       column1="wizard_id",
                                       column2="city_id",
                                       string='Cities')

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            res = {'city_ids': active_ids}
        return res

    @api.multi
    def batch_end_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        cities = self.env['hs.sales.city'].search([('id', 'in', active_ids)])
        for city in cities:
            city.write({'province_id': self.env['hs.sales.province'].search([
                ('province_number', '=', city.province_number)], limit=1).id})
        return {'type': 'ir.actions.act_window_close'}


class HSSalesNote(models.Model):
    _name = 'hs.sales.note'
    _inherit = ['mail.thread']
    _description = '日志'
    _order = 'workday desc'

    @api.model
    def _get_default_employee(self):
        return self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char(string='标题', required=True, track_visibility='onchange')
    workday = fields.Datetime(string='时间', required=True, default=fields.Datetime.now,
                              track_visibility='onchange')
    employee_id = fields.Many2one('hs.base.employee', string='员工', required=True,
                                  default=_get_default_employee,
                                  ondelete='restrict',
                                  track_visibility='onchange')
    # province_id = fields.Many2one(comodel_name="hs.sales.province", string="省", required=True, )
    province_id = fields.Many2one(
        'res.country.state', '省', domain="[('country_id.code', '=', 'CN')]", required=True,)

    # city_id = fields.Many2one(comodel_name="hs.sales.city", string="市", required=True, )
    city_id = fields.Many2one(comodel_name="res.city", string="市", required=True, )
    customer_id = fields.Many2one(comodel_name="hs.sales.customer", string="客户名称",
                                  track_visibility='onchange')
    contact_name = fields.Char(string="联系人名称", )
    contact_title = fields.Char(string="联系人职务", )
    contact_number = fields.Char(string="联系人电话", )
    work_category = fields.Selection(string="工作类型", selection=[
        ('tel', '业务开拓 - 电话'),
        ('email', '业务开拓 - 电子邮件'),
        ('scene', '业务开拓 - 现场拜访'),
        ('entertain', '业务开拓 - 招待'),
        ('order', '订单处理'),
        ('quality', '质量处理'),
        ('other', '其他'), ], required=True, track_visibility='onchange')
    description = fields.Html('描述', track_visibility='onchange')

    @api.onchange('province_id')
    def onchange_province_id(self):
        value = dict()
        value['domain'] = dict()
        self.city_id = False
        if self.province_id and self.province_id is not None:
            domain = [('state_id', '=', self.province_id.id)]
            value['domain']['city_id'] = domain
        return value
