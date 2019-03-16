# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
# from odoo.addons import decimal_precision as dp


class EntertainCompany(models.Model):
    _name = 'hs.expense.entertain.company'
    _inherits = {"res.partner": "partner_id"}
    _rec_name = 'name'

    partner_id = fields.Many2one(string="Partner", comodel_name='res.partner', required=True, ondelete='cascade')
    is_entertain_company = fields.Boolean(string="Is Entertain Company", default=True)

    @api.model
    def create(self, vals):
        vals['is_company'] = True
        return super(EntertainCompany, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name') or vals.get('name') is not None:
            partner = self.partner_id
            partner.write({'name': vals.get('name')})
        return super(EntertainCompany, self).write(vals)

    @api.multi
    def unlink(self):
        partner = self.partner_id
        super(EntertainCompany, self).unlink()
        return partner.unlink()


class EntertainUser(models.Model):
    _name = 'hs.expense.entertain.user'
    _inherits = {"res.partner": "partner_id"}
    _rec_name = 'display_name'

    partner_id = fields.Many2one(string="Partner", comodel_name='res.partner', required=True, ondelete='cascade')
    is_entertain_user = fields.Boolean(string="Is Entertain User", default=True)
    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('partner_id', 'name', 'parent_id.name')
    def _compute_display_name(self):
        for res in self:
            names = [res.partner_id.parent_id.name, res.partner_id.name]
            res.display_name = ','.join(names)

    @api.model
    def create(self, vals):
        vals['is_company'] = False
        return super(EntertainUser, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('name') or vals.get('name') is not None:
            partner = self.partner_id
            partner.write({'name': vals.get('name')})
        return super(EntertainUser, self).write(vals)

    @api.multi
    def unlink(self):
        partner = self.partner_id
        super(EntertainUser, self).unlink()
        return partner.unlink()


class Seller(models.Model):
    _inherit = 'hs.base.employee'

    sale_market_id = fields.Many2one('hs.sale.market', string='Sale Market')
    sale_area_id = fields.Many2one('hs.sale.area', string='Sale Area')
    bank_name = fields.Char(string='Bank Name')
    bank_account = fields.Char(string='Bank Account')


class SaleMarket(models.Model):
    _name = 'hs.sale.market'
    _description = 'Sale Market'

    name = fields.Char()
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string='Active', default=True)

    sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name already exists!'),
    ]


class SaleArea(models.Model):
    _name = 'hs.sale.area'
    _description = 'Sale Area'

    name = fields.Char()
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string='Active', default=True)

    sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name already exists!'),
    ]


class SpecialApplication(models.Model):
    _name = 'hs.expense.special.application'
    _description = 'Special application and reimbursement form'

    applicant_id = fields.Many2one('hs.base.employee', string='Applicant') #申请人
    handler_id = fields.Many2one('hs.base.employee', string='Handler') #报销经办人
    applicant_date = fields.Date(string='Application Date') #申请日期
    applicant_department_id = fields.Many2one('hs.base.department', related='applicant_id.department_id')
    entertain_company_id = fields.Many2one('res.partner', string='Entertain Company',
                                           domain="[('is_entertain_company', '=', True)]")
    entertain_res_user_id = fields.Many2many('res.partner', string='Entertain Company',
                                             domain="[('parent_id', '=', entertain_company_id.parent_id)]")
    applicant_amount = fields.Float("Applicant Amount", required=True,
                                    # digits=lambda self: self.env['decimal.precision'].precision_get('Product Price'))
                                    digits=(16, 2))
    # lambda self: self.env.ref('base.main_company').id
    cause = fields.Text(string="Cause")
    sale_area_id = fields.Many2one('hs.sale.area', related='applicant_id.sale_area_id', string='Sale Area')
    sale_market_id = fields.Many2one('hs.sale.market', related='applicant_id.sale_market_id', string='Sale Market')

    reimbursement_person_id = fields.Many2one(related='handler_id', string="Reimbursement")
    reimbursement_payment_method = fields.Selection(
        [('cash', 'Cash'), ('mt', 'Money Transfer')],
        string='Payment Method', default='mt')
    bank_name = fields.Char(related='reimbursement_person_id.bank_name', string='Bank Name')
    bank_account = fields.Char(related='reimbursement_person_id.bank_account', string='Bank Account')
    reimbursement_amount = fields.Float(
        "Reimbursement Amount",
        required=True,
        states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]},
        digits=(16,2))

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('approved', 'Approved'),
        ('done', 'Paid'),
        ('refused', 'Refused')
    ], string='Status', copy=False, index=True, readonly=True, store=True,
        help="Status of the expense.")