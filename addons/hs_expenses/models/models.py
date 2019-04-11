# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
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
            if res.partner_id is not None and res.partner_id.parent_id is not None:
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
    _inherit = ['hs.base.employee']

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
    _order = 'applicant_date desc, id desc'
    # _rec_name = 'complete_name'

    @api.model
    def _get_default_employee(self):
        return self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    def _get_company_partner_domain(self):
        ids = []
        if self.entertain_company_id:
            ids = [self.entertain_company_id.partner_id.id]
        else:
            ids = [x['partner_id'][0] for x in self.env['hs.expense.entertain.company'].sudo().search_read(
                [(1, '=', 1)], ['partner_id'])]
        return [('partner_id.parent_id', 'in', ids)]

    @api.onchange('entertain_company_id')
    def onchange_entertain_company_id(self):
        if self.entertain_res_user_ids:
            self.entertain_res_user_ids = None
        result = {}
        domain = self._get_company_partner_domain()
        result['domain'] = {'entertain_res_user_ids': domain}
        return result

    @api.onchange('applicant_amount')
    def onchange_applicant_amount(self):
        for s in self:
            s.reimbursement_amount = s.applicant_amount

    @api.onchange('handler_id')
    def onchange_handler_id(self):
        for s in self:
            s.reimbursement_person_id = s.handler_id
            s.bank_name = s.handler_id.bank_name
            s.bank_account = s.handler_id.bank_account

    @api.onchange('applicant_id')
    def onchange_applicant_id(self):
        for s in self:
            s.handler_id = s.applicant_id
            s.sale_area_id = s.applicant_id.sale_area_id
            s.sale_market_id = s.applicant_id.sale_market_id

    @api.depends('cause', 'applicant_id', 'applicant_amount')
    def _compute_complete_name(self):
        if self.cause:
            self.complete_name = '[ %s ] %s - %.2f' % (self.cause if self.cause else '',
                                                       self.applicant_id.complete_name,
                                                       self.applicant_amount)
        else:
            self.complete_name = '%s - %.2f' % (self.applicant_id.complete_name,
                                                self.applicant_amount)

    @api.one
    @api.depends('countersign_ids')
    def _compute_current_sign_completed(self):
        self.current_sign_completed = False
        current_employee = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        for sign in self.countersign_ids:
            if sign.employee_id.id == current_employee.id:
                self.current_sign_completed = sign.is_approved

    name = fields.Char(string="Bill Number", require=True)
    complete_name = fields.Char(compute='_compute_complete_name', string='Complete Name')
    applicant_id = fields.Many2one('hs.base.employee', string='Applicant', required=True, default=_get_default_employee) #申请人
    handler_id = fields.Many2one('hs.base.employee', string='Handler', required=True, default=_get_default_employee) #报销经办人
    applicant_date = fields.Date(string='Application Date', required=True, default=lambda self: fields.Date.context_today(self)) #申请日期
    applicant_department_id = fields.Many2one('hs.base.department', related='applicant_id.department_id', store=True)
    entertain_company_id = fields.Many2one('hs.expense.entertain.company', string='Entertain Company', required=True,
                                           domain="[('is_entertain_company', '=', True)]")
    entertain_res_user_ids = fields.Many2many('hs.expense.entertain.user', string='Entertain Person',
                                              domain=_get_company_partner_domain)
    applicant_amount = fields.Float("Applicant Amount", required=True, digits=(16, 2))
    cause = fields.Text(string="Cause")
    sale_area_id = fields.Many2one('hs.sale.area', related='applicant_id.sale_area_id', string='Sale Area', store=True)
    sale_market_id = fields.Many2one('hs.sale.market', related='applicant_id.sale_market_id', string='Sale Market', store=True)

    reimbursement_person_id = fields.Many2one('hs.base.employee', string="Reimbursement Person", required=True)
    reimbursement_payment_method = fields.Selection(
        [('cash', 'Cash'), ('mt', 'Money Transfer')],
        string='Payment Method', default='mt')
    bank_name = fields.Char(string='Bank Name')
    bank_account = fields.Char(string='Bank Account')
    reimbursement_amount = fields.Float(
        "Reimbursement Amount",
        required=True,
        digits=(16, 2))

    # have_to_countersign = fields.Boolean(default=False)
    complete_countersign = fields.Boolean(default=False)
    # countersign_ids = fields.Many2many('hs.expense.countersign', 'hs_expense_app_sign_rel',
    #                                    'expense_id', 'countersign_id', string='Countersign', readonly=True)
    countersign_ids = fields.One2many('hs.expense.countersign', 'expense_id', string='Countersign', readonly=True)

    current_sign_completed = fields.Boolean(compute='_compute_current_sign_completed')

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('approved', 'Approved'),
        ('confirmed', 'Confirmed '),
        ('audited', 'Audited'),
        ('audited2', 'Cashier Audited'),
        ('countersign', 'Countersign'),
        ('done', 'Paid')
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='draft',
        help="Status of the expense.")

    expense_category = fields.Selection([
        ('quality', 'Quality'),
        ('contract', 'Contract order delivery'),
        ('project', 'New project development'),
        ('other', 'Other'),
    ], string='Category', index=True, default='other', required=True)

    @api.model
    def create(self, vals):
        if vals.get('name') is None:
            name = self.env['ir.sequence'].next_by_code('hs.expense.special.application.no')
            if not name:
                self.env['ir.sequence'].sudo().create({
                    'number_next': 1,
                    'number_increment': 1,
                    'padding': 8,
                    'prefix': 'SA',
                    'name': 'Special Application NO.',
                    'code': 'hs.expense.special.application.no',
                })
                name = self.env['ir.sequence'].next_by_code('hs.expense.special.application.no')
            vals['name'] = name
        return super(SpecialApplication, self).create(vals)

    @api.multi
    def write(self, vals):
        # employee = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        # if self.handler_id.id != employee.id:
        #     raise UserError(_("You are not the handler!"))
        # if vals:
        #     if self.state not in ['draft', 'approved']:
        #         raise UserError(_("You cannot modify the application that have already been submitted!"))

        return super(SpecialApplication, self).write(vals)

    @api.multi
    def unlink(self):
        employee = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        for expense in self:
            if expense.state not in ['draft']:
                raise UserError(_('You cannot delete a posted or approved expense.'))
            if expense.create_uid.id != self.env.uid:
                raise UserError(_("You cannot delete the expense!"))
        return super(SpecialApplication, self).unlink()

    @api.multi
    def action_submit_expenses(self): # 营销人员草稿状态提交到领导审批
        if any(expense.state != 'draft' for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        self.write({'state': 'reported'})
        return True

    @api.multi
    def action_approve_expenses(self): # 领导审批完成，提交到报销经办人申请报销（填写报销相关内容）
        if any(expense.state != 'reported' for expense in self):
            raise UserError(_("You cannot approve twice the same line!"))
        self.write({'state': 'approved'})
        return True

    @api.multi
    def action_back_to_draft(self):
        if any(expense.state != 'reported' for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))
        self.write({'state': 'draft'})
        return True

    @api.multi
    def action_confirm_expenses(self): # 报销经办人填写好后提交到领导审批
        employee = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        if any(expense.state != 'approved' for expense in self):
            raise UserError(_("You cannot confirm twice the same line!"))
        if self.handler_id._uid != self.env.uid:
            raise UserError(_("You are not the handler!"))
        self.write({'state': 'confirmed'})
        return True

    @api.multi
    def action_audit_expenses(self): # 领导审批完成，提交给财务审核
        if any(expense.state != 'confirmed' for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))
        self.write({'state': 'audited'})
        return True

    @api.multi
    def action_back_to_confirm(self):
        if any(expense.state != 'confirmed' for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))
        self.write({'state': 'approved'})
        return True

    @api.multi
    def action_audit2_expenses(self): # 财务审核完成，提交给出纳
        if any(expense.state != 'audited' for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))

        if self.reimbursement_amount >= 5000:
            group_id = self.env.ref('hs_expenses.group_hs_expenses_leader').id
            leaders = self.env['res.users'].search([('groups_id', '=', group_id)])
            countersign = self.env['hs.expense.countersign']
            for leader in leaders:
                employee = self.env['hs.base.employee'].search([('user_id', '=', leader.id)], limit=1)
                if employee and not leader.has_group('hs_expenses.group_hs_expenses_manager'):
                    countersign.sudo().create({
                        'employee_id': employee.id,
                        'expense_id': self.id
                    })
        self.write({'state': 'audited2'})
        return True

    @api.multi
    def action_cashier_expenses(self):
        if any(expense.state != 'audited2' for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))
        if self.reimbursement_amount >= 5000:
            if not self.complete_countersign:
                self.write({'state': 'countersign'})
            else:
                self.action_done_expenses()
        else:
            self.action_done_expenses()
        return True

    @api.multi
    def function_countersign_expenses(self):
        employee = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        if employee and employee is not None:
            expense_id = self
            countersign = self.env['hs.expense.countersign'].search(
                [('employee_id', '=', employee.id), ('expense_id', '=', expense_id.id)], limit=1)
            if countersign and countersign is not None:
                countersign.write({'is_approved': True})
            else:
                raise UserError(_("Some errors have occurred in the system!"))

            if not any(sign.is_approved is False
                       for sign in self.env['hs.expense.countersign'].search([('expense_id', '=', expense_id.id)])):
                self.write({'complete_countersign': True, 'state': 'audited2'})
                # self.action_done_expenses()
        return True

    # todo: 出纳需要判断金额是否大于5000,大于5000需要会签，5000以内直接放款结束流程
    @api.multi
    def action_done_expenses(self):
        if any(expense.state not in ['audited2', 'countersign'] for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))
        if self.reimbursement_amount < 5000:
            self.write({'state': 'done'})
        else:
            if self.complete_countersign:
                self.write({'state': 'done'})
        return True


class CounterSign(models.Model):
    _name = 'hs.expense.countersign'
    _description = 'Countersign'

    employee_id = fields.Many2one('hs.base.employee', string='Employee', required=True)
    # expense_ids = fields.Many2many('hs.expense.special.application', 'hs_expense_app_sign_rel',
    #                               'countersign_id', 'expense_id', string='Special Application')
    expense_id = fields.Many2one('hs.expense.special.application', string='Special Application')
    is_approved = fields.Boolean(default=False)
