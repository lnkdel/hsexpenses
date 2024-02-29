# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class TravelStandard(models.Model):
    _name = 'hs.expense.travel.standard'
    _description = 'Travel Standard'

    travel_category_id = fields.Many2one('hs.expense.travel.category', string='Travel Category', required=True)
    employee_level_id = fields.Many2one('hs.base.employee.level', string='Employee Level', required=True)
    city_level_id = fields.Many2one('hs.base.city.level', string='City Level', required=True)
    standard_meal_cost = fields.Float("Standard Meal Cost", digits=(16, 2))
    standard_hotel_cost = fields.Float("Standard Hotel Cost", digits=(16, 2))
    standard_car_cost = fields.Float("Standard Car Cost", digits=(16, 2))
    remark = fields.Text()


class EmployeeLevel(models.Model):
    _name = 'hs.base.employee.level'
    _description = 'Employee Level'

    name = fields.Char(required=True)


class City(models.Model):
    _name = 'hs.base.city'

    name = fields.Char()
    city_level_id = fields.Many2one('hs.base.city.level', string='City Level')
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('city_name_uniq',
         'unique (name)',
         'The city has the same records.')
    ]


class CityLevel(models.Model):
    _name = 'hs.base.city.level'
    _description = 'City Level'

    name = fields.Char(required=True)
    city_ids = fields.One2many('hs.base.city', 'city_level_id', string='Cities')
    active = fields.Boolean(string='Active', default=True)


class TravelCategory(models.Model):
    _name = 'hs.expense.travel.category'
    _description = 'Travel Category'

    name = fields.Char(required=True)

