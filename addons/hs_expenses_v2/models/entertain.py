# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class EntertainApplication(models.Model):
    _name = 'hs.expense.v2.entertain.application'
    _inherit = 'hs.expense.v2.base.application'
    _description = 'Entertain application and reimbursement form'
    _order = 'applicant_date desc, id desc'

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

    @api.onchange('reimbursement_amount')
    def onchange_reimbursement_amount(self):
        for s in self:
            if s.reimbursement_amount > s.applicant_amount:
                s.reimbursement_amount = s.applicant_amount
                raise UserError(_("Reimbursement amount must be less than or equal to the application amount!"))

    @api.onchange('applicant_id')
    def onchange_applicant_id(self):
        for s in self:
            s.reimbursement_person_id = s.applicant_id
            s.bank_name = s.applicant_id.bank_name
            s.bank_account = s.applicant_id.bank_account
            s.sale_area_id = s.applicant_id.sale_area_id
            s.sale_market_id = s.applicant_id.sale_market_id
            if s.applicant_id.department_id:
                if '技术服务' in s.applicant_id.department_id.name:
                    category_quality = self.env['hs.expense.category'].search([('name', '=', '质量')], limit=1)
                    if category_quality:
                        s.expense_category_ids = category_quality

    @api.one
    @api.depends('countersign_ids')
    def _compute_current_sign_completed(self):
        self.current_sign_completed = False
        current_employee = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        for sign in self.countersign_ids:
            if sign.employee_id.id == current_employee.id:
                self.current_sign_completed = sign.is_approved

    def _compute_current_user_is_financial(self):
        self.current_user_is_financial = self.user_has_groups('hs_expenses.group_hs_expenses_financial_officer')

    # entertain_company_id = fields.Many2one('hs.expense.entertain.company', string='Entertain Company', required=True,
    #                                        domain="[('is_entertain_company', '=', True)]")
    # entertain_res_user_ids = fields.Many2many('hs.expense.entertain.user',
    #                                           'entertain_user_v2_entertain_app_rel',
    #                                           'entertain_app_id',
    #                                           'entertain_user_id',
    #                                           string='Entertain Person',
    #                                           domain=_get_company_partner_domain)

    customer_company_no = fields.Many2one('hs.base.customer.number', required=True, string='Customer Company Number')
    customer_count = fields.Integer(string='Customer Count', default=1)

    entertain_date = fields.Date(string='Entertain Date', required=True,
                                 default=lambda self: fields.Date.context_today(self))
    applicant_amount = fields.Float("Applicant Amount", required=True, digits=(16, 2))

    reimbursement_amount = fields.Float(
        "Reimbursement Amount",
        required=True,
        digits=(16, 2))
    reimbursement_remark = fields.Text(string="Reimbursement Remark")

    audit_amount = fields.Float("Audit Amount", digits=(16, 2))
    current_user_is_financial = fields.Boolean(compute="_compute_current_user_is_financial")

    complete_countersign = fields.Boolean(default=False)
    countersign_ids = fields.One2many('hs.expense.v2.countersign.entertain', 'expense_id', string='Countersign',
                                      readonly=True)
    # back_ids = fields.One2many('hs.expense.v2.entertain.back.dialog', 'expense_id', string='Back List', readonly=True)

    current_sign_completed = fields.Boolean(compute='_compute_current_sign_completed')

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('reported2', 'Submitted2'),
        ('approved', 'Approved'),
        ('confirmed', 'Confirmed'),
        ('audited', 'Audited'),
        ('countersign', 'Countersign'),
        ('done', 'Paid')
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='draft',
        help="Status of the expense.")

    expense_category_ids = fields.Many2many(comodel_name="hs.expense.category",
                                            relation="hs_expense_entertain_category_rel",
                                            column1="entertain_id",
                                            column2="category_id",
                                            string="Category",
                                            required=True)

    attachment_ids = fields.Many2many('ir.attachment',
                                      'hs_expense_entertain_app_rel',
                                      'entertain_app_id',
                                      'attachment_id',
                                      string='Attachments')
    project_id = fields.Many2one('hs.base.project', string='Project')

    @api.model
    def create(self, vals):
        if vals.get('name') is None:
            name = self.env['ir.sequence'].next_by_code('hs.expense.v2.entertain.app.no')
            if not name:
                self.env['ir.sequence'].sudo().create({
                    'number_next': 1,
                    'number_increment': 1,
                    'padding': 7,
                    'prefix': 'E',
                    'name': 'Entertain Application NO.',
                    'code': 'hs.expense.v2.entertain.app.no',
                })
                name = self.env['ir.sequence'].next_by_code('hs.expense.v2.entertain.app.no')
            vals['name'] = name
        # if vals.get('customer_name') is None:
        #     vals['customer_name'] = vals.get('customer_company_no') or 'xx'
        return super(EntertainApplication, self).create(vals)

    @api.multi
    def write(self, vals):
        return super(EntertainApplication, self).write(vals)

    @api.multi
    def unlink(self):
        for expense in self:
            if expense.state not in ['draft']:
                raise UserError(_('You cannot delete a posted or approved expense.'))
            if expense.create_uid.id != self.env.uid:
                raise UserError(_("You cannot delete the expense!"))
        return super(EntertainApplication, self).unlink()

    @api.multi
    def action_submit_expenses(self): # 营销人员草稿状态提交到领导审批
        if any(expense.state != 'draft' for expense in self):
            raise UserError(_("You cannot report twice the same line!"))

        countersign = self.env['hs.expense.v2.countersign.entertain']
        reviewers = []

        for category in self.expense_category_ids:
            if category.name == '质量':
                group_id = self.env.ref('hs_expenses.group_hs_expenses_quality_reviewer').id
            elif category.name == '合同订单发货回款':
                group_id = self.env.ref('hs_expenses.group_hs_expenses_contract_reviewer').id
            elif category.name == '新项目拓展':
                group_id = self.env.ref('hs_expenses.group_hs_expenses_project_reviewer').id
            elif category.name == '其他':
                group_id = self.env.ref('hs_expenses.group_hs_expenses_other_reviewer').id
            elif category.name == '补充申请':
                group_id = self.env.ref('hs_expenses.group_hs_expenses_project_reviewer').id
            reviewers.append(self.env['res.users'].search([('groups_id', '=', group_id)]))

        countersign.sudo().search(
            [('expense_id', '=', self.id), ('is_approved', '=', False)]).unlink()
        countersigns = countersign.sudo().search([('expense_id', '=', self.id)]).read([('employee_id')])
        lst = [cc['employee_id'][0] for cc in countersigns]

        for reviewer in reviewers:
            for user in reviewer:
                employee = self.env['hs.base.employee'].search([('user_id', '=', user.id)], limit=1)
                if employee and not user.has_group('hs_expenses.group_hs_expenses_manager'):
                    if employee.id not in lst:
                        countersign.sudo().create({
                            'employee_id': employee.id,
                            'expense_id': self.id
                        })

        # if not any(sign.is_approved is True for sign in countersign.sudo().search([('expense_id', '=', self.id)])):
        if all(sign.is_approved is True for sign in countersign.sudo().search([('expense_id', '=', self.id)])):
            self.write({'state': 'reported2'})
        else:
            self.write({'state': 'reported'})
        return True

    @api.multi
    def action_reported2_expenses(self): # 领导审批完成，提交到副总裁
        if any(expense.state != 'reported' for expense in self):
            raise UserError(_("You cannot approve twice the same line!"))

        employee = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        if employee and employee is not None:
            expense_id = self
            countersign = self.env['hs.expense.v2.countersign.entertain'].search(
                [('employee_id', '=', employee.id), ('expense_id', '=', expense_id.id)], limit=1)
            if countersign and countersign is not None:
                countersign.write({'is_approved': True})
            else:
                raise UserError(_("Some errors have occurred in the system!"))

            if not any(sign.is_approved is False
                       for sign in self.env['hs.expense.v2.countersign.entertain'].search([('expense_id', '=', expense_id.id)])):
                self.write({'complete_countersign': True, 'state': 'reported2'})

        return True

    @api.multi
    def action_approved_expenses(self):  # 副总裁审批完成，提交到报销经办人申请报销（填写报销相关内容）
        if any(expense.state != 'reported2' for expense in self):
            raise UserError(_("You cannot approve twice the same line!"))
        self.write({'state': 'approved'})
        return True

    @api.multi
    def action_back_to_draft(self):
        self.write({'state': 'draft'})
        return True

    @api.multi
    def action_confirm_expenses(self): # 报销经办人填写好后提交到财务审批
        if any(expense.state != 'approved' for expense in self):
            raise UserError(_("You cannot confirm twice the same line!"))

        if self.reimbursement_amount > self.applicant_amount:
            raise UserError(_("Reimbursement amount must be less than or equal to the application amount!"))

        self.write({'state': 'confirmed'})
        return True

    @api.multi
    def action_back_to_confirm(self): # 财务退回上一步
        if any(expense.state != 'confirmed' for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))
        self.write({'state': 'approved'})
        return True

    @api.multi
    def action_audit_expenses(self): # 财务审核完成，提交给出纳
        if any(expense.state != 'confirmed' for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))

        if self.audit_amount <= 0:
            raise UserError(_("Please enter the correct audit amount!"))

        self.write({'state': 'audited', 'audit_date': datetime.now()})
        return True

    @api.multi
    def action_cashier_expenses(self): # 放款结束流程
        if any(expense.state != 'audited' for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))
        self.action_done_expenses()
        return True

    @api.multi
    def function_countersign_expenses(self):
        employee = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        if employee and employee is not None:
            expense_id = self
            countersign = self.env['hs.expense.v2.countersign.entertain'].search(
                [('employee_id', '=', employee.id), ('expense_id', '=', expense_id.id)], limit=1)
            if countersign and countersign is not None:
                countersign.write({'is_approved': True})
            else:
                raise UserError(_("Some errors have occurred in the system!"))

            if not any(sign.is_approved is False
                       for sign in
                       self.env['hs.expense.v2.countersign.entertain'].search([('expense_id', '=', expense_id.id)])):
                self.write({'complete_countersign': True, 'state': 'audited'})
                # self.action_done_expenses()
        return True

    @api.multi
    def action_done_expenses(self):
        if any(expense.state not in ['audited'] for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))

        self.write({'state': 'done'})
        return True

    @api.multi
    def action_back_to_to_audited(self):  # 出纳退回给财务审核
        self.write({'state': 'confirmed'})


class BackDialog(models.Model):
    _name = 'hs.expense.v2.entertain.back.dialog'
    _description = 'Back Dialog'

    @api.model
    def _get_default_employee(self):
        return self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    cause = fields.Text()
    operator = fields.Many2one('hs.base.employee', string='Applicant', required=True, default=_get_default_employee)
    operate_date = fields.Datetime(string='Operate Date', default=datetime.now().strftime('%Y-%m-%d'))
    expense_id = fields.Many2one('hs.expense.v2.entertain.application', string='Entertain Application')

    def do_confirm(self):
        self.create({'cause': self.cause, 'operator': self.operator, 'operate_date': self.operate_date,
                     'expense_id': self.expense_id})


class BatchEndEntertainApplicationWizard(models.TransientModel):
    _name = 'hs.expense.v2.entertain.batch.end.wizard'
    _description = 'Batch end application wizard'

    application_ids = fields.Many2many(comodel_name='hs.expense.v2.entertain.application',
                                       relation="hs_expense_v2_end_wizard_entertain_rel",
                                       column1="wizard_id",
                                       column2="application_id",
                                       string='Entertain Applications')

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            applications = self.env['hs.expense.v2.entertain.application'].search_read(
                domain=[('id', 'in', active_ids)], fields=['id', 'state'])
            ids = [s['id'] for s in list(filter(lambda s: s['state'] == 'audited', applications))]
            res = {'application_ids': ids}
        return res

    @api.multi
    def batch_end_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        applications = self.env['hs.expense.v2.entertain.application'].search([
            ('id', 'in', active_ids),
            ('state', '=', 'audited')])
        applications.write({'state': 'done'})
        return {'type': 'ir.actions.act_window_close'}


class CounterSignMonthV2(models.Model):
    _name = 'hs.expense.v2.countersign.entertain'
    _description = 'Entertain Countersign'

    employee_id = fields.Many2one('hs.base.employee', string='Employee', required=True)
    expense_id = fields.Many2one('hs.expense.v2.entertain.application', string='Entertain Application')
    is_approved = fields.Boolean(default=False)