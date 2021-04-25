# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SalesLead(models.Model):
    _name = 'hs.sales.lead'
    _inherit = ['mail.thread']
    _rec_name = 'lead_number'
    _description = 'Sales Lead'
    _order = 'lead_number DESC'

    @api.model
    def _get_default_employee(self):
        return self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char(required=True, string="机会点名称", track_visibility='onchange')
    state = fields.Selection(string="状态", selection=[
        ('Open', 'Open-开始'),
        ('Active', 'Active-进行中'),
        ('Delay', 'Delay-延期'),
        ('CTS', 'CTS-转销售'),
        ('Failure', 'Failure-失败'),], required=True, default='Open', track_visibility='onchange')
    sale_manager_id = fields.Many2one('hs.base.employee', string='销售经理', required=True,
                                   default=_get_default_employee, track_visibility='onchange')
    lead_number = fields.Char(string="机会编号", required=True, )
    lead_value = fields.Float(string="机会价值",  required=True, track_visibility='onchange' )
    success_probability = fields.Float(string="成功概率(%)", required=True, default=50,
                                       track_visibility='onchange')
    priority = fields.Selection(string="优先级", selection=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),], required=True, default="medium", track_visibility='onchange')
    sale_market_id = fields.Many2one('hs.sale.market', string='应用市场', required=True,
                                     track_visibility='onchange')
    customer_id = fields.Many2one(comodel_name="hs.sales.customer", string="客户名称", required=True,
                                  track_visibility='onchange' )
    source = fields.Selection(string="机会来源", selection=[
        ('introduction', '现有客户介绍'),
        ('new', '现有客户新项目'),
        ('expo', '研讨会/展会'),
        ('university', '科研院所/大学推荐'), ], required=True, track_visibility='onchange')
    completion_time = fields.Date(string='计划完成时间', required=True,
                                  default=lambda self: fields.Date.context_today(self),
                                  track_visibility='onchange')
    technical_service_manager_id = fields.Many2one('hs.base.employee',
                                                   string='技术服务经理',
                                                   domain=['|', ('department_id.name', 'ilike', '营销'), ('department_id.parent_id.name', 'ilike', '营销')],
                                                   track_visibility='onchange' )
    customer_service_manager_id = fields.Many2one('hs.base.employee',
                                                  string='客户服务经理',
                                                  track_visibility='onchange' )
    reason = fields.Selection(string="失败原因", selection=[
        ('exit', '战略退出'),
        ('price', '价格不具竞争力'),
        ('product', '产品不胜任'),
        ('technical', '技术不胜任'),
        ('time', '交期不胜任'),
    ], required=False, track_visibility='onchange' )
    remark = fields.Text(string="备注", required=False, )
    lead_description = fields.Text(string="机会价值描述", required=False, )
    shrink_name = fields.Char(string='机会点名称', compute='_compute_shrink_name')

    user_name = fields.Char(string="最终用户名称", required=False, )
    contact_name = fields.Char(string="联系人名称", required=True)
    contact_title = fields.Char(string="联系人职务", required=True, )
    contact_number = fields.Char(string="联系人电话", required=True, )
    contact_email = fields.Char(string="电子邮箱", required=False, )
    customer_city = fields.Char(string="客户所在省市", required=True, )
    customer_address = fields.Char(string="客户详细地址", required=True, )
    color = fields.Integer()

    @api.model
    def create(self, values):
        if values.get('lead_number') is None or values.get('lead_number') is False:
            lead_number = self.env['ir.sequence'].next_by_code('hs.sales.lead.no')
            values['lead_number'] = lead_number

        return super(SalesLead, self).create(values)
    
    @api.one
    @api.depends('name')
    def _compute_shrink_name(self):
        for rec in self:
            rec.shrink_name = (rec.name[:20]+'...') if len(rec.name)>20 else rec.name

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        for rec in self:
            rec.contact_name = rec.customer_id.contact_name
            rec.contact_title = rec.customer_id.contact_title
            rec.contact_number = rec.customer_id.contact_number
            rec.contact_email = rec.customer_id.contact_email
            address = rec.customer_id.address
            rec.customer_address = address
            rec.customer_city = ''
            if address:
                index = address.find('市')
                if index != -1:
                    rec.customer_city = address[:index+1]
                else:
                    rec.customer_city = rec.customer_id.city
            else:
                rec.customer_city = rec.customer_id.city

    def show_lead_detail_form(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'target': self,
            'res_model': 'hs.sales.lead',
            'res_id': self.id,
            'name': 'Sales Lead'
        }
        return action




