# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Customer(models.Model):
    _name = 'hs.sales.customer'
    _rec_name = 'name'
    _description = '客户'

    name = fields.Char(string="客户名称", required=True, )
    group_id = fields.Many2one(comodel_name="hs.sales.customer", string="客户所属集团", required=False, )
    address = fields.Char(string="所在地", required=False, )
    user_name = fields.Char(string="最终用户名", required=False, )
    contact_name = fields.Char(string="联系人名称", required=False, )
    contact_title = fields.Char(string="联系人职务", required=False, )
    contact_number = fields.Char(string="联系人电话", required=False, )
    contact_email = fields.Char(string="电子邮箱", required=False, )
    sequence = fields.Integer(string="排序")
    active = fields.Boolean(string="有效?", default=True)

    _sql_constraints = [
        ('name_unique','unique(name)',
         "该客户已经存在！")
    ]