# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
# from datetime import datetime

import datetime
from datetime import date


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
            if s.applicant_id.sale_market_id:
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
    customer_count = fields.Integer(string='Customer Count', default=1, required=True)

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

    entertain_type = fields.Selection([
        ('business hospitality1', '商务招待1档（600元/人）'),
        ('business hospitality2', '商务招待2档（500元/人）'),
        ('business hospitality3', '商务招待3档（400元/人）'),
        ('official hospitality', '公务招待（160元/人）'),
        ('souvenir', '纪念品（600元/人）'),
        ('default', ''),
    ], string='招待类型', required=True, default='default')

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
    entertain_remark = fields.Text(string="Entertain Remark", default="单位：\n部门、职位及人员：\n")

    feedback_number_id = fields.Many2one(comodel_name="hs.sales.customer.feedback.number", string="客户反馈编码")

    cause_type = fields.Selection([
        ('bos', 'Business on sale'),
        ('pa', 'Project approval'),
        ('ho', 'Have opportunities'),
        ('potential', 'Potential')
    ], string='Cause Type', default='bos', required=True)
    reason = fields.Text()
    approved_records = fields.Text()
    sale_group_id = fields.Many2one('hs.expense.sale.group', string='销售市场组')

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

        entertain_remark = vals.get('entertain_remark')
        is_pass = True
        if entertain_remark is None:
            raise UserError(_('Please input the entertain information on the field of entertain_remark.'))
        else:
            entertain_remark = entertain_remark.strip()
            if entertain_remark.find('单位：') > -1 and entertain_remark.find('部门、职位及人员：') > -1:
                infos = entertain_remark.split('\n')
                for info in infos:
                    if info.find('：') > 0:
                        if info.split('：')[1].strip() is '':
                            is_pass = False
                            break
                    else:
                        is_pass = False
                        break
            else:
                is_pass = False
        if not is_pass:
            raise UserError(_('Please input the entertain information on the field of entertain_remark.'))
        return super(EntertainApplication, self).create(vals)

    @api.multi
    def write(self, vals):
        if self.state == 'draft':
            is_pass = True
            entertain_remark = ''
            if vals.get('entertain_remark') is None:
                entertain_remark = self.entertain_remark
            else:
                entertain_remark = vals.get('entertain_remark').strip()

            if entertain_remark.find('单位：') > -1 and entertain_remark.find('部门、职位及人员：') > -1:
                infos = entertain_remark.split('\n', 1)
                for info in infos:
                    if info.find('：') > 0:
                        if info.split('：')[1].strip() is '':
                            is_pass = False
                            break
                    else:
                        is_pass = False
                        break
            else:
                is_pass = False

            if not is_pass:
                raise UserError(_('Please input the entertain information on the field of entertain_remark.'))
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

        entertain_standard_dict = {'business hospitality1': 600, 'business hospitality2': 500,
                                   'business hospitality3': 400, 'official hospitality': 160,
                                   'souvenir': 600}
        if self.entertain_type == 'default':
            raise UserError(_("招待类型不能为NULL！"))
        elif self.customer_count and self.applicant_amount and \
                self.applicant_amount > entertain_standard_dict[self.entertain_type] * int(self.customer_count):
            raise UserError(_("申请金额超标！"))

        countersign = self.env['hs.expense.v2.countersign.entertain']
        reviewers = []

        employee_id = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)])
        result = self.env['hs.expense.travel.audit'].sudo().search([('name', '=', employee_id.id),
                                                                    ('sale_group_id', '=', self.sale_group_id.id)])
        if result:
            if result.audit_type < 3:
                user_id = result.first_audit.id
            else:
                user_id = result.second_audit.id
            reviewers.append(user_id)
        else:
            raise UserError(_("该用户该销售市场组无对应审批人，请联系管理员设置!"))

        countersign.sudo().search([('expense_id', '=', self.id)]).unlink()
        countersigns = countersign.sudo().search([('expense_id', '=', self.id)]).read([('employee_id')])
        lst = [cc['employee_id'][0] for cc in countersigns]

        for user in reviewers:
            if user not in lst:
                countersign.sudo().create({
                    'employee_id': user,
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

        approved_text = self.record_approve()

        self.write({'state': 'approved', 'approved_records': approved_text})
        return True

    @api.multi
    def action_back_to_draft(self):
        # self.write({'state': 'draft'})
        # return True
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hs.expense.v2.entertain.back.wizard',
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

        approved_text = self.record_approve()

        self.write({'audit_amount': self.reimbursement_amount, 'state': 'confirmed', 'approved_records': approved_text})
        return True

    @api.multi
    def action_back_to_confirm(self): # 财务退回上一步
        # if any(expense.state != 'confirmed' for expense in self):
        #     raise UserError(_("You cannot audit twice the same line!"))
        # self.write({'state': 'approved'})
        # return True
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hs.expense.v2.entertain.back.wizard',
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

        approved_text = self.record_approve()

        self.write({'state': 'audited', 'audit_date': datetime.datetime.now(),
                    'approved_records': approved_text})
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
        # self.write({'state': 'confirmed'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hs.expense.v2.entertain.back.wizard',
            'name': '退回向导',
            'view_mode': 'form',
            'context': {
                'application_id': self.id,
                'default_state': 'confirmed',
            },
            'target': 'new'
        }

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

    def _next_state(self, name):
        if name == 'reported2':
            return 'approved'
        elif name == 'approved':
            return 'confirmed'
        elif name == 'confirmed':
            return 'audited'

    def record_approve(self):  # 记录审核过程
        operator = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

        origin_state = self._tranlate_state_name(self.state)
        now_state = self._tranlate_state_name(self._next_state(self.state))

        approved_text = '%s   %s ---> %s' % \
                        (operator.complete_name if operator.complete_name else 'Administrator',
                         origin_state,
                         now_state)
        if self.approved_records:
            approved_text = self.approved_records + '\n\n' + approved_text
        return approved_text

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        domain = self.get_own_forecast_domain(domain)
        return super(EntertainApplication, self).search_read(domain, fields, offset, limit, order)

    def get_own_forecast_domain(self, domain=None):
        user_domain = domain or []
        env = self.env
        user_id = env.uid
        if self.user_has_groups('hs_expenses.group_hs_expenses_manager'):
            own_domain = [(1, '=', 1)]
        else:
            employee = env['hs.base.employee'].sudo().search([('user_id', '=', user_id)])
            countersigns = env['hs.expense.v2.countersign.entertain'].sudo().search([('employee_id', '=', employee.id)])
            expense_ids = [countersign.expense_id for countersign in countersigns]
            names = [application.name for application in expense_ids]
            if self.user_has_groups('hs_expenses_v2.group_hs_expenses_travel_application_approver'):
                if self.user_has_groups('hs_expenses_v2.group_hs_expenses_vice_president'):
                    own_domain = ['|', '|', ('create_uid.id', '=', user_id), '&', ('name', 'in', names),
                                  ('state', '=', 'reported'), ('state', '=', 'reported2')]
                else:
                    own_domain = ['|', ('create_uid.id', '=', user_id), '&', ('name', 'in', names),
                                  ('state', '=', 'reported')]
            elif self.user_has_groups('hs_expenses.group_hs_expenses_financial_officer'):
                own_domain = [('state', 'in', ['confirmed', 'audited'])]
            elif self.user_has_groups('hs_expenses.group_hs_expenses_cashier'):
                own_domain = [('state', 'in', ['audited', 'done'])]
            else:
                own_domain = [('create_uid.id', '=', user_id)]
        return user_domain + own_domain

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain = self.get_own_forecast_domain(domain)
        return super(EntertainApplication, self.with_context(virtual_id=False)).read_group(domain, fields, groupby,
                                                                                         offset=offset, limit=limit,
                                                                                         orderby=orderby, lazy=lazy)


class EntertainApplicationBackWizard(models.TransientModel):
    _name = 'hs.expense.v2.entertain.back.wizard'
    _description = 'Entertain application back wizard'

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
        app = self.env['hs.expense.v2.entertain.application'].browse(int(application_id))
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


class BatchApprovedEntertainApplicationWizard(models.TransientModel): # 王胜利要求批量审批 20220711
    _name = 'hs.expense.v2.entertain.batch.approve.wizard'
    _description = 'Batch approve application wizard'

    application_ids = fields.Many2many(comodel_name='hs.expense.v2.entertain.application',
                                       relation="hs_expense_v2_approve_wizard_entertain_rel",
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
            ids = [s['id'] for s in list(filter(lambda s: s['state'] == 'reported2', applications))]
            res = {'application_ids': ids}
        return res

    @api.multi
    def batch_approve_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        applications = self.env['hs.expense.v2.entertain.application'].search([
            ('id', 'in', active_ids),
            ('state', '=', 'reported2')])
        operator = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        for app in applications:
            origin_state = '已审阅'
            now_state = '已批准'

            approved_text = '%s - %s \n%s ---> %s' % \
                            (operator.complete_name if operator.complete_name else 'Administrator',
                             (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
                             origin_state,
                             now_state)
            if app.approved_records:
                approved_text = app.approved_records + '\n\n' + approved_text
            app.write({'state': 'approved', 'approved_records': approved_text})
        return {'type': 'ir.actions.act_window_close'}


class BatchauditedEntertainApplicationWizard(models.TransientModel): # 财务周锦来要求批量审核 20231101
    _name = 'hs.expense.v2.entertain.batch.audit.wizard'
    _description = 'Batch Audit application wizard'

    application_ids = fields.Many2many(comodel_name='hs.expense.v2.entertain.application',
                                       relation="hs_expense_v2_audit_wizard_entertain_rel",
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
            ids = [s['id'] for s in list(filter(lambda s: s['state'] == 'confirmed', applications))]
            res = {'application_ids': ids}
        return res

    @api.multi
    def batch_audit_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        applications = self.env['hs.expense.v2.entertain.application'].search([
            ('id', 'in', active_ids),
            ('state', '=', 'confirmed')])
        operator = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        for app in applications:
            origin_state = '已确认'
            now_state = '已审核'

            approved_text = '%s - %s \n%s ---> %s' % \
                            (operator.complete_name if operator.complete_name else 'Administrator',
                             (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
                             origin_state,
                             now_state)
            if app.approved_records:
                approved_text = app.approved_records + '\n\n' + approved_text
            app.write({'state': 'audited', 'approved_records': approved_text})
        return {'type': 'ir.actions.act_window_close'}


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
        for app in applications:
            app.write({'state': 'done'})
        return {'type': 'ir.actions.act_window_close'}


class CounterSignMonthV2(models.Model):
    _name = 'hs.expense.v2.countersign.entertain'
    _description = 'Entertain Countersign'

    employee_id = fields.Many2one('hs.base.employee', string='Employee', required=True)
    expense_id = fields.Many2one('hs.expense.v2.entertain.application', string='Entertain Application')
    is_approved = fields.Boolean(default=False)