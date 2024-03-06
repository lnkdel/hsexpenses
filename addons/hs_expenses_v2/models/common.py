# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class Project(models.Model):
    _name = 'hs.base.project'
    _description = 'Project'

    name = fields.Char(required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string='Active', default=True)


class DriverType(models.Model):
    _name = 'hs.base.driver.type'
    _description = 'Driver Type'

    name = fields.Char(required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string='Active', default=True)


class CustomerCompanyNO(models.Model):
    _name = 'hs.base.customer.number'
    _description = 'Customer Number'

    name = fields.Char(required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string='Active', default=True)


class FeedBackNO(models.Model):
    _name = 'hs.sales.customer.feedback.number'
    _description = '客户反馈编码'

    name = fields.Char(required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string='Active', default=True)


class TravelAudit(models.Model):
    _name = 'hs.expense.travel.audit'
    _description = 'Travel Audit'

    name = fields.Many2one('hs.base.employee', string='申请人', required=True)
    sale_group_id = fields.Many2one('hs.expense.sale.group', string='销售市场组', required=True)
    first_audit = fields.Many2one('hs.base.employee', string='一级审批人', required=True)
    second_audit = fields.Many2one('hs.base.employee', string='二级审批人')
    third_audit = fields.Many2one('hs.base.employee', string='三级审批人')
    audit_type = fields.Integer(string='审批级别', required=True)

    @api.constrains('name', 'sale_group_id')
    def _check(self):
        result = self.env['hs.expense.travel.audit'].sudo().search([('name', '=', self.name.id),
                                                                    ('sale_group_id', '=', self.sale_group_id.id)])
        if len(result) > 1:
            raise UserError(_("该申请人对应销售市场组审批人已存在!"))


class SaleGroup(models.Model):
    _name = 'hs.expense.sale.group'
    _description = 'Sale Group'

    name = fields.Char(string='销售市场组', required=True)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', '该销售市场组已存在!'),
    ]
