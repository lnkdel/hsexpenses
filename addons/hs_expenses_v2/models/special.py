# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime
from datetime import date


class SpecialApplication(models.Model):
    _name = 'hs.expense.v2.special.application'
    _inherit = 'hs.expense.v2.base.application'
    _description = 'Special application and reimbursement form'
    _order = 'applicant_date desc, id desc'

    @api.model
    def _get_default_employee(self):
        return self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

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

    customer_company_no = fields.Many2one('hs.base.customer.number', string='Customer Company Number')
    customer_count = fields.Integer(string='Customer Count', default=0)

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
    countersign_ids = fields.One2many('hs.expense.v2.countersign.special', 'expense_id', string='Countersign',
                                      readonly=True)

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
                                            relation="hs_expense_v2_special_category_rel",
                                            column1="special_id",
                                            column2="category_id",
                                            string="Category",
                                            required=True)

    attachment_ids = fields.Many2many('ir.attachment',
                                      'hs_expense_v2_special_app_rel',
                                      'special_app_id',
                                      'attachment_id',
                                      string='Attachments')
    project_id = fields.Many2one('hs.base.project', string='Project')
    reason = fields.Text()

    @api.model
    def create(self, vals):
        if vals.get('name') is None:
            name = self.env['ir.sequence'].next_by_code('hs.expense.v2.special.app.no')
            if not name:
                self.env['ir.sequence'].sudo().create({
                    'number_next': 1,
                    'number_increment': 1,
                    'padding': 7,
                    'prefix': 'S',
                    'name': 'Special Application NO.',
                    'code': 'hs.expense.v2.special.app.no',
                })
                name = self.env['ir.sequence'].next_by_code('hs.expense.v2.special.app.no')
            vals['name'] = name
            if vals.get('expense_category_ids') is None:
                vals['expense_category_ids'] = [[6, False, [3]]]
        return super(SpecialApplication, self).create(vals)

    @api.multi
    def write(self, vals):
        return super(SpecialApplication, self).write(vals)

    @api.multi
    def unlink(self):
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

        countersign = self.env['hs.expense.v2.countersign.special']
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
            countersign = self.env['hs.expense.v2.countersign.special'].search(
                [('employee_id', '=', employee.id), ('expense_id', '=', expense_id.id)], limit=1)
            if countersign and countersign is not None:
                countersign.write({'is_approved': True})
            else:
                raise UserError(_("Some errors have occurred in the system!"))

            if not any(sign.is_approved is False
                       for sign in self.env['hs.expense.v2.countersign.special'].search([('expense_id', '=', expense_id.id)])):
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
        # self.write({'state': 'draft'})
        # return True
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hs.expense.v2.special.back.wizard',
            'name': '退回向导',
            'view_mode': 'form',
            'context': {
                'application_id': self.id,
                'default_state': 'draft',
            },
            'target': 'new'
        }

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
        # if any(expense.state != 'confirmed' for expense in self):
        #     raise UserError(_("You cannot audit twice the same line!"))
        # self.write({'state': 'approved'})
        # return True
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hs.expense.v2.special.back.wizard',
            'name': '退回向导',
            'view_mode': 'form',
            'context': {
                'application_id': self.id,
                'default_state': 'approved',
            },
            'target': 'new'
        }

    @api.multi
    def action_audit_expenses(self): # 财务审核完成，提交给出纳
        if any(expense.state != 'confirmed' for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))

        if self.audit_amount <= 0:
            raise UserError(_("Please enter the correct audit amount!"))

        self.write({'state': 'audited', 'audit_date': datetime.datetime.now()})
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
            countersign = self.env['hs.expense.v2.countersign.special'].search(
                [('employee_id', '=', employee.id), ('expense_id', '=', expense_id.id)], limit=1)
            if countersign and countersign is not None:
                countersign.write({'is_approved': True})
            else:
                raise UserError(_("Some errors have occurred in the system!"))

            if not any(sign.is_approved is False
                       for sign in
                       self.env['hs.expense.v2.countersign.special'].search([('expense_id', '=', expense_id.id)])):
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
        # self.write({'state': 'confirmed'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hs.expense.v2.special.back.wizard',
            'name': '退回向导',
            'view_mode': 'form',
            'context': {
                'application_id': self.id,
                'default_state': 'confirmed',
            },
            'target': 'new'
        }


class SpecialApplicationBackWizard(models.TransientModel):
    _name = 'hs.expense.v2.special.back.wizard'
    _description = 'Special application back wizard'

    reason = fields.Text()
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

    def _tranlate_state_name(self, name):
        if name == 'draft':
            return '待提交'
        elif name == 'reported':
            return '已提交'
        elif name == 'reported2':
            return '已审阅'
        elif name == 'approved':
            return '已批准'
        elif name == 'confirmed':
            return '已确认'
        elif name == 'audited':
            return '已审核'
        elif name == 'countersign':
            return '会签'
        elif name == 'done':
            return '已支付'

    def save_button(self):
        application_id = self.env.context.get('application_id')
        app = self.env['hs.expense.v2.special.application'].browse(int(application_id))
        operator = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

        origin_state = self._tranlate_state_name(app.state)
        now_state = self._tranlate_state_name(self.state)

        reason_text = '备注: %s - %s \n%s ---> %s\n%s' % \
                      (operator.complete_name,
                       (datetime.datetime.now()+datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
                       origin_state,
                       now_state,
                       self.reason if self.reason else '无')
        if app.reason:
            reason_text = app.reason + '\n\n' + reason_text
        app.write({'reason': reason_text, 'state': self.state})
        return True


class BatchEndApplicationWizard(models.TransientModel):
    _name = 'hs.expense.v2.batch.end.wizard'
    _description = 'Batch end application wizard'

    application_ids = fields.Many2many(comodel_name='hs.expense.v2.special.application',
                                       relation="hs_expense_v2_end_wizard_special_rel",
                                       column1="wizard_id",
                                       column2="application_id",
                                       string='Special Applications')

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            applications = self.env['hs.expense.v2.special.application'].search_read(
                domain=[('id', 'in', active_ids)], fields=['id', 'state'])
            ids = [s['id'] for s in list(filter(lambda s: s['state'] == 'audited', applications))]
            res = {'application_ids': ids}
        return res

    @api.multi
    def batch_end_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        applications = self.env['hs.expense.v2.special.application'].search([
            ('id', 'in', active_ids),
            ('state', '=', 'audited')])
        for app in applications:
            app.write({'state': 'done'})
        return {'type': 'ir.actions.act_window_close'}


class CounterSignMonthV2(models.Model):
    _name = 'hs.expense.v2.countersign.special'
    _description = 'Special Countersign'

    employee_id = fields.Many2one('hs.base.employee', string='Employee', required=True)
    expense_id = fields.Many2one('hs.expense.v2.special.application', string='Special Application')
    is_approved = fields.Boolean(default=False)