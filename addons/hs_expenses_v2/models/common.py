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