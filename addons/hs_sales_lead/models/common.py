# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Customer(models.Model):
    _name = 'hs.sales.customer'
    _description = '客户'

    name = fields.Char(string="客户名称", required=True, )
    group_id = fields.Many2one(comodel_name="hs.sales.customer", string="客户所属集团", required=False,)
    city = fields.Char(string="所在省市", required=True, )
    address = fields.Char(string="详细地址", required=True, )
    contact_name = fields.Char(string="联系人名称", required=False, )
    contact_title = fields.Char(string="联系人职务", required=False, )
    contact_number = fields.Char(string="联系人电话", required=False, )
    contact_email = fields.Char(string="电子邮箱", required=False, )
    sequence = fields.Integer(string="排序")
    active = fields.Boolean(string="有效?", default=True)

    _sql_constraints = [
        ('name_unique','unique(name, contact_name)',
         "该客户已经存在！")
    ]

    @api.multi
    @api.depends('group_id')
    def name_get(self):
        res = []
        for rec in self:
            names = [rec.name]
            parent_record = rec.group_id
            while parent_record:
                names.append(parent_record.name)
                parent_record = parent_record.group_id
            res.append((rec.id, ' - '.join(reversed(names))))
        return res
