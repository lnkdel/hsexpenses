# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


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

    def _compute_current_month_quota(self):
        for seller in self:
            seller.current_month_quota = 0
            today = fields.Date.today()
            year = today.year
            month = today.month - 1
            if month == 0:
                year = year - 1
                month = 12

            last_month_benefit = self.env['hs.sale.benefit'].sudo().\
                search([('employee_id', '=', seller.id), ('year', '=', year), ('month', '=', month)])

            if last_month_benefit:
                seller.current_month_quota = last_month_benefit[0]['benefit']

    @api.depends('current_month_quota', 'current_month_quota_used')
    def _compute_current_month_quota_remained(self):
        for seller in self:
            seller.current_month_quota_remained = seller.current_month_quota - seller.current_month_quota_used

    sale_market_id = fields.Many2one('hs.sale.market', string='Sale Market')
    sale_area_id = fields.Many2one('hs.sale.area', string='Sale Area')
    bank_name = fields.Char(string='Bank Name')
    bank_account = fields.Char(string='Bank Account')
    employee_level_id = fields.Many2one('hs.base.employee.level', string='Employee Level')
    current_month_quota = fields.Float("Current Month Quota", required=True, digits=(16, 2),
                                       compute='_compute_current_month_quota')
    current_month_quota_used = fields.Float("Current Month Quota Used", required=True, digits=(16, 2),
                                            default=0, readonly=True)
    current_month_quota_remained = fields.Float("Current Month Quota remained", required=True, digits=(16, 2),
                                                compute='_compute_current_month_quota_remained')
    special_quota = fields.Float("Special Quota", required=True, digits=(16, 2), default=200000)
    special_quota_used = fields.Float("Special Quota Used", required=True, digits=(16, 2), default=0, readonly=True)


class Benefit(models.Model):
    _name = 'hs.sale.benefit'
    _description = 'Sale Benefit'
    _order = 'year desc, month desc'

    employee_id = fields.Many2one('hs.base.employee', string='Employee', required=True)
    year = fields.Integer(default=fields.Date.today().year, required=True)
    month = fields.Integer(default=fields.Date.today().month, required=True)
    benefit = fields.Float("Benefit", required=True, digits=(16, 2))
    remark = fields.Text()

    _sql_constraints = [
        ('employee_year_month_uniq',
         'unique (employee_id,year,month)',
         'The month has the same records.')
    ]


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


class ExpenseCategory(models.Model):
    _name = 'hs.expense.category'
    _description = 'Expense Category'

    name = fields.Char()
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Category name already exists!'),
    ]


class SpecialApplication(models.Model):
    _name = 'hs.expense.special.application'
    _description = 'Special application and reimbursement form'
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
            if s.applicant_id.department_id:
                if '技术服务' in s.applicant_id.department_id.name:
                    category_quality = self.env['hs.expense.category'].search([('name', '=', '质量')], limit=1)
                    if category_quality:
                        s.expense_category_ids = category_quality

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

    def _compute_current_user_is_financial(self):
        self.current_user_is_financial = self.user_has_groups('hs_expenses.group_hs_expenses_financial_officer')

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
    entertain_date = fields.Date(string='Entertain Date', required=True,
                                 default=lambda self: fields.Date.context_today(self))
    applicant_amount = fields.Float("Applicant Amount", required=True, digits=(16, 2))
    cause = fields.Text(string="Cause", required=True)
    application_remark = fields.Text(string="Application Remark")

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
    reimbursement_remark = fields.Text(string="Reimbursement Remark")

    audit_amount = fields.Float("Audit Amount", digits=(16, 2))
    current_user_is_financial = fields.Boolean(compute="_compute_current_user_is_financial")

    complete_countersign = fields.Boolean(default=False)
    countersign_ids = fields.One2many('hs.expense.countersign', 'expense_id', string='Countersign', readonly=True)

    current_sign_completed = fields.Boolean(compute='_compute_current_sign_completed')
    # 批准后减去额度
    approved_deduction_amount = fields.Float("Approved Deduction Amount", digits=(16, 2))
    # 审计后减去额度
    audited_deduction_amount = fields.Float("Audited Deduction Amount", digits=(16, 2))

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('approved', 'Approved'),
        ('confirmed', 'Confirmed '),
        ('audited', 'Audited'),
        # ('audited2', 'Cashier Audited'),
        ('countersign', 'Countersign'),
        ('done', 'Paid')
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='draft',
        help="Status of the expense.")

    expense_category = fields.Selection([
        ('quality', 'Quality'),
        ('contract', 'Contract order delivery'),
        ('project', 'New project development'),
        ('other', 'Other'),
        ('supplement', 'Supplementary application'),
    ], string='Category', index=True, default='other', required=True)
    expense_category_ids = fields.Many2many(comodel_name="hs.expense.category",
                                            relation="hs_expense_special_category_rel",
                                            column1="special_id",
                                            column2="category_id",
                                            string="Category",
                                            required=True)
    # attachment_file_name = fields.Char(string='Attachment')
    # attachment_file = fields.Binary(string='Attachment', attachment=True)
    attachment_ids = fields.Many2many('ir.attachment', 'hs_expense_special_app_rel', 'special_app_id', 'attachment_id', string='Attachments')
    audit_date = fields.Datetime(string='Audit Date')

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
        if self.applicant_amount <= 2000:
            raise UserError(_("For applications within 2,000 yuan, please use the ordinary hospitality application."))
        # elif self.applicant_amount > 10000:
        #     raise UserError(_("The amount of a single application cannot exceed 10,000 yuan."))
        # 2019-9-12 要求暂时去掉10000限制，应对中秋送礼

        special_quota_used = self.applicant_id.special_quota_used
        special_quota = self.applicant_id.special_quota
        if special_quota_used + self.applicant_amount > special_quota:
            # raise UserError(_("The accumulated application amount within one year shall not exceed %.2f yuan."
            #                   "You have used %.2f yuan this year."
            #                   "Please modify the application amount." %
            #                   (special_quota, special_quota_used)))
            # raise UserError(_("一年内累计申请金额不得超过 {quota} 元。今年你已经使用了 {quota_used} 元。请修改申请金额。"
            #                   .format(quota=special_quota, quota_used=special_quota_used)))
            raise UserError(_("The accumulated application amount within one year shall not exceed {quota} yuan."
                              "You have used {quota_used} yuan this year."
                              "Please modify the application amount."
                              .format(quota=special_quota, quota_used=special_quota_used)))

        countersign = self.env['hs.expense.countersign']
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
        self.write({'state': 'reported'})
        return True

    @api.multi
    def action_approve_expenses(self): # 领导审批完成，提交到报销经办人申请报销（填写报销相关内容）
        if any(expense.state != 'reported' for expense in self):
            raise UserError(_("You cannot approve twice the same line!"))

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
                self.write({'complete_countersign': True, 'state': 'approved'})

                # 批准 记录已使用额度
                # if self.approved_deduction_amount == 0:
                #     self.applicant_id.special_quota_used += self.applicant_amount
                # else:
                #     if self.applicant_amount != self.approved_deduction_amount:
                #         difference = abs(self.applicant_amount - self.approved_deduction_amount)
                #         if self.applicant_amount > self.approved_deduction_amount:
                #             self.applicant_id.special_quota_used += difference
                #         else:
                #             self.applicant_id.special_quota_used -= difference
                #             if self.applicant_id.special_quota_used < 0:
                #                 self.applicant_id.special_quota_used = 0
                #
                # self.approved_deduction_amount = self.applicant_amount

        # self.write({'state': 'approved'})
        return True

    @api.multi
    def action_back_to_draft(self):
        if any(expense.state != 'reported' for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))

        # 退回 释放已使用额度
        # if self.approved_deduction_amount != 0:
        #     self.applicant_id.special_quota_used -= self.approved_deduction_amount
        #     if self.applicant_id.special_quota_used < 0:
        #         self.applicant_id.special_quota_used = 0
        #     self.approved_deduction_amount = 0

        self.write({'state': 'draft'})
        return True

    @api.multi
    def action_confirm_expenses(self): # 报销经办人填写好后提交到财务审批
        today = fields.Date.today()
        if today.day < 23:
            raise UserError(_("Please submit after 23 days of each month."))

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

        # 审计退回， 释放审计金额占用额度
        if self.audited_deduction_amount != 0:
            if self.audited_deduction_amount != self.approved_deduction_amount:
                difference = abs(self.audited_deduction_amount - self.approved_deduction_amount)
                if self.audited_deduction_amount > self.approved_deduction_amount:
                    self.applicant_id.special_quota_used -= difference
                    if self.applicant_id.special_quota_used < 0:
                        self.applicant_id.special_quota_used = 0
                else:
                    self.applicant_id.special_quota_used += difference

            self.audited_deduction_amount = 0

        self.write({'state': 'approved'})
        return True

    @api.multi
    def action_audit_expenses(self): # 财务审核完成，提交给出纳
        if any(expense.state != 'confirmed' for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))

        if self.audit_amount <= 0:
            raise UserError(_("Please enter the correct audit amount!"))

        # 生成会签条件
        if self.audit_amount >= 5000:
            group_id = self.env.ref('hs_expenses.group_hs_expenses_leader').id
            leaders = self.env['res.users'].search([('groups_id', '=', group_id)])
            countersign = self.env['hs.expense.countersign']
            # current_countersign_list = self.env['hs.expense.countersign'].search([('expense_id', '=', self.id)])

            current_countersigns = countersign.sudo().search([('expense_id', '=', self.id)]).read([('employee_id')])
            lst = [cc['employee_id'][0] for cc in current_countersigns]

            for leader in leaders:
                employee = self.env['hs.base.employee'].search([('user_id', '=', leader.id)], limit=1)
                if employee and not leader.has_group('hs_expenses.group_hs_expenses_manager'):
                    if employee.id not in lst:
                        countersign.sudo().create({
                            'employee_id': employee.id,
                            'expense_id': self.id
                        })

        # 根据审核金额 调整特殊招待全年申请额度
        if self.audited_deduction_amount == 0:
            if self.audit_amount != self.approved_deduction_amount:
                ded_difference = abs(self.audit_amount - self.approved_deduction_amount)
                if self.audit_amount > self.approved_deduction_amount:
                    self.applicant_id.special_quota_used += ded_difference
                else:
                    self.applicant_id.special_quota_used -= ded_difference
                    if self.applicant_id.special_quota_used < 0:
                        self.applicant_id.special_quota_used = 0
        else:
            if self.audit_amount != self.audited_deduction_amount:
                difference = abs(self.audited_deduction_amount - self.audit_amount)
                if self.audit_amount > self.audited_deduction_amount:
                    self.applicant_id.special_quota_used += difference
                else:
                    self.applicant_id.special_quota_used -= difference
                    if self.applicant_id.special_quota_used < 0:
                        self.applicant_id.special_quota_used = 0

        self.audited_deduction_amount = self.audit_amount

        if self.audit_amount < 5000:
            self.write({'state': 'audited', 'audit_date': datetime.now()})
        else:
            self.write({'state': 'countersign', 'audit_date': datetime.now()})
        return True

    @api.multi
    def action_cashier_expenses(self): # 审核金额>=5000出纳提交会签，否则放款结束流程
        if any(expense.state != 'audited' for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))
        # if self.audit_amount >= 5000:
        #     if not self.complete_countersign:
        #         self.write({'state': 'countersign'})
        #     else:
        #         self.action_done_expenses()
        # else:
        #     self.action_done_expenses()
        # 去掉会签
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
                self.write({'complete_countersign': True, 'state': 'audited'})
                # self.action_done_expenses()
        return True

    # 出纳需要判断金额是否大于5000,大于5000需要会签，5000以内直接放款结束流程  --20190417 与姜烨确认去掉会签
    @api.multi
    def action_done_expenses(self):
        if any(expense.state not in ['audited', 'countersign'] for expense in self):
            raise UserError(_("You cannot audit twice the same line!"))
        # if self.audit_amount < 5000:
        #     self.write({'state': 'done'})
        # else:
        #     if self.complete_countersign:
        #         self.write({'state': 'done'})
        # 去掉会签
        self.write({'state': 'done'})
        return True

    @api.multi
    def action_back_to_to_audited(self):  # 出纳退回给财务审核
        self.write({'state': 'confirmed'})


class CounterSign(models.Model):
    _name = 'hs.expense.countersign'
    _description = 'Countersign'

    employee_id = fields.Many2one('hs.base.employee', string='Employee', required=True)
    expense_id = fields.Many2one('hs.expense.special.application', string='Special Application')
    is_approved = fields.Boolean(default=False)


class BatchEndApplicationWizard(models.TransientModel):
    _name = 'hs.expense.batch.end.wizard'
    _description = 'Batch end application wizard'

    application_ids = fields.Many2many('hs.expense.special.application', string='Special Applications')

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            applications = self.env['hs.expense.special.application'].search_read(
                domain=[('id', 'in', active_ids)], fields=['id', 'state'])
            ids = [s['id'] for s in list(filter(lambda s: s['state'] == 'audited', applications))]
            res = {'application_ids': ids}
        return res

    @api.multi
    def batch_end_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        applications = self.env['hs.expense.special.application'].search([
            ('id', 'in', active_ids),
            ('state', '=', 'audited')])
        applications.write({'state': 'done'})
        return {'type': 'ir.actions.act_window_close'}
