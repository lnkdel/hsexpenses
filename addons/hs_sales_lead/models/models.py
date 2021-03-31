# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SalesLead(models.Model):
    _name = 'hs.sales.lead'
    _rec_name = 'lead_number'
    _description = 'Sales Lead'

    @api.model
    def _get_default_employee(self):
        return self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char(required=True)
    state = fields.Selection(string="状态", selection=[
        ('Open', 'Open-开始'),
        ('Active', 'Active-进行中'),
        ('Delay', 'Delay-延期'),
        ('CTS', 'CTS-转销售'),
        ('Failure', 'Failure-失败'),], required=True, default='Open')
    sale_manager_id = fields.Many2one('hs.base.employee', string='销售经理', required=True,
                                   default=_get_default_employee)
    lead_number = fields.Char(string="机会编号", required=True, )
    lead_value = fields.Float(string="机会价值",  required=True, )
    success_probability = fields.Float(string="成功概率", required=True, default=50)
    priority = fields.Selection(string="优先级", selection=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),], required=True, default="medium")
    sale_market_id = fields.Many2one('hs.sale.market', string='应用市场',)
    customer_id = fields.Many2one(comodel_name="hs.sales.customer", string="客户", required=True, )
    source = fields.Selection(string="机会来源", selection=[
        ('introduction', '现有客户介绍'),
        ('new', '现有客户新项目'),
        ('expo', '研讨会/展会'),
        ('university', '科研院所/大学推荐'), ], required=True, )
    completion_time = fields.Datetime(string="计划完成时间", required=True, default=fields.Datetime.now())
    technical_service_manager_id = fields.Many2one('hs.base.employee', string='技术服务经理', )
    customer_service_manager_id = fields.Many2one('hs.base.employee', string='客户服务经理', )
    reason = fields.Selection(string="失败原因", selection=[
        ('exit', '战略退出'),
        ('price', '价格不具竞争力'),
        ('product', '产品不胜任'),
        ('technical', '技术不胜任'),
        ('time', '交期不胜任'),
    ], required=False, )
    remark = fields.Text(string="备注", required=False, )
    shrink_name = fields.Char(string='Name', compute='_compute_shrink_name')

    @api.model
    def create(self, values):
        if values.get('lead_number') is None or values.get('lead_number') is False:
            lead_number = self.env['ir.sequence'].next_by_code('hs.sales.lead.no')
            if not lead_number:
                self.env['ir.sequence'].sudo().create({
                    'number_next': 1,
                    'number_increment': 1,
                    'padding': 7,
                    'prefix': 'L',
                    'name': 'Sales Lead NO.',
                    'code': 'hs.sales.lead.no',
                })
                lead_number = self.env['ir.sequence'].next_by_code('hs.sales.lead.no')
            values['lead_number'] = lead_number
        return super(SalesLead, self).create(values)
    
    @api.one
    @api.depends('name')
    def _compute_shrink_name(self):
        for rec in self:
            rec.shrink_name = (rec.name[:10]+'...') if len(rec.name)>20 else rec.name

