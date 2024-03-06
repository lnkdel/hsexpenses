from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
# from datetime import datetime
import datetime
from datetime import date
import calendar


class Travel2Application(models.Model):
    _name = 'hs.expense.v2.travel2.application'
    _inherit = 'hs.expense.v2.base.application'
    _description = 'Travel2 expenses reimbursement form'
    _order = 'applicant_date desc, id desc'

    @api.depends('travel_detail_ids')
    def _compute_audit_amount(self):
        for travel in self:
            if travel.travel_detail_ids is not None or travel.travel_detail_ids is not False:
                for detail in travel.travel_detail_ids:
                    travel.audit_amount += detail.audit_amount
                    travel.audit_cut_amount += detail.audit_cut_amount

    @api.depends('travel_detail_ids')
    def _compute_meal_total_cost(self):
        for travel in self:
            if travel.travel_detail_ids is not None or travel.travel_detail_ids is not False:
                for detail in travel.travel_detail_ids:
                    travel.meal_total_cost += detail.meal_cost

    @api.depends('travel_detail_ids')
    def _compute_hotel_total_cost(self):
        for travel in self:
            if travel.travel_detail_ids is not None or travel.travel_detail_ids is not False:
                for detail in travel.travel_detail_ids:
                    travel.hotel_total_cost += detail.hotel_cost

    @api.depends('travel_detail_ids')
    def _compute_car_total_cost(self):
        for travel in self:
            if travel.travel_detail_ids is not None or travel.travel_detail_ids is not False:
                for detail in travel.travel_detail_ids:
                    travel.car_total_cost += detail.car_cost

    @api.depends('travel_detail_ids')
    def _compute_city_car_total_cost(self):
        for travel in self:
            if travel.travel_detail_ids is not None or travel.travel_detail_ids is not False:
                for detail in travel.travel_detail_ids:
                    travel.city_car_total_cost += detail.city_car_cost

    @api.depends('total_cost')
    def _compute_total_cost(self):
        for travel in self:
            travel.total_cost = travel.meal_total_cost + travel.hotel_total_cost \
                                + travel.car_total_cost + travel.city_car_total_cost

    def _compute_current_user_is_financial(self):
        self.current_user_is_financial = self.user_has_groups('hs_expenses.group_hs_expenses_financial_officer')

    @api.onchange('audit_cut_amount')
    def _onchange_audit_cut_amount(self):
        for travel in self:
            for de in travel.travel_detail_ids:
                de.audit_amount = de.total_cost - de.audit_cut_amount
            travel.audit_amount = travel.total_cost - travel.audit_cut_amount

    destination_city = fields.Many2one("hs.base.city", string="出差目的地", required=True)
    travel_detail_ids = fields.One2many('hs.expense.v2.travel2.detail', 'travel_application_id',
                                        string='Travel Details')
    state = fields.Selection([
        ('travel_draft', '待提交'),
        ('travel_to_audited', '待审核'),
        ('first_audited', '已审核'),
        ('draft', '已批准'),
        ('to_audited', '已确认'),
        ('audited', '财务审核'),
        ('done', '已支付')
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='travel_draft',
        help="Status of the expense.")

    travel_start_date = fields.Date(string='出差开始时间', required=True,
                                    default=lambda self: fields.Date.context_today(self))
    travel_end_date = fields.Date(string='出差结束时间', required=True,
                                  default=lambda self: fields.Date.context_today(self))
    travel_transportation = fields.Selection([
        ('train', '火车'),
        ('airplane', '飞机'),
        ('car', '汽车'),
        ('other', '其他')
    ], string='出差交通工具', required=True, default='train')
    reimbursement_remark = fields.Text(string="Reimbursement Remark")
    sale_group_id = fields.Many2one('hs.expense.sale.group', string='销售市场组', required=True)
    first_auditor_id = fields.Many2one('hs.base.employee', string='一级审批人')
    second_auditor_id = fields.Many2one('hs.base.employee', string='二级审批人')

    meal_total_cost = fields.Float("Total Meal Cost", compute="_compute_meal_total_cost", digits=(16, 2))
    hotel_total_cost = fields.Float("Total Hotel Cost", compute="_compute_hotel_total_cost", digits=(16, 2))
    car_total_cost = fields.Float("Total Car Cost", compute="_compute_car_total_cost", digits=(16, 2))
    city_car_total_cost = fields.Float("Total City Car Cost", compute="_compute_city_car_total_cost", digits=(16, 2))
    total_cost = fields.Float("Total Cost", compute="_compute_total_cost", digits=(16, 2))

    audit_amount = fields.Float("Audit Amount", digits=(16, 2), compute="_compute_audit_amount")
    audit_cut_amount = fields.Float("Audit Cut Amount", digits=(16, 2), compute="_compute_audit_amount")
    audit_remark = fields.Text(string="Audit Remark")
    current_user_is_financial = fields.Boolean(compute="_compute_current_user_is_financial")
    customer_company_no = fields.Many2one('hs.base.customer.number', string='Customer Company Number')
    reason = fields.Text(string="退回理由")

    attachment_ids = fields.Many2many('ir.attachment',
                                      'hs_expense_travel2_app_rel',
                                      'travel_app_id',
                                      'attachment_id',
                                      string='出差报告')
    approved_records = fields.Text(string="审批记录")

    @api.model
    def create(self, values):
        if values.get('name') is None or values.get('name') is False:
            name = self.env['ir.sequence'].next_by_code('hs.expense.v2.travel.app.no')
            if not name:
                self.env['ir.sequence'].sudo().create({
                    'number_next': 1,
                    'number_increment': 1,
                    'padding': 7,
                    'prefix': 'T',
                    'name': 'Travel Application NO.',
                    'code': 'hs.expense.v2.travel2.app.no',
                })
                name = self.env['ir.sequence'].next_by_code('hs.expense.v2.travel2.app.no')
            values['name'] = name
        employee_id = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)])
        result = self.env['hs.expense.travel.audit'].sudo().search([('name', '=', employee_id.id),
                                                                    ('sale_group_id', '=', values['sale_group_id'])])
        if result:
            values['first_auditor_id'] = result.first_audit.id
            values['second_auditor_id'] = result.second_audit.id
        else:
            raise UserError(_("该用户该销售市场组无对于审批人，请联系管理员设置!"))
        return super(Travel2Application, self).create(values)

    @api.multi
    def write(self, values):
        # Add code here
        employee_id = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)])
        result = self.env['hs.expense.travel.audit'].sudo().search([('name', '=', employee_id.id),
                                                                    ('sale_group_id', '=', self.sale_group_id.id)])
        if result:
            values['first_auditor_id'] = result.first_audit.id
            values['second_auditor_id'] = result.second_audit.id
        else:
            raise UserError(_("该用户该销售市场组无对于审批人，请联系管理员设置!"))
        return super(Travel2Application, self).write(values)

    @api.multi
    def unlink(self):
        for expense in self:
            if expense.state not in ['travel_draft']:
                raise UserError(_('You cannot delete a posted or approved expense.'))
            if expense.create_uid.id != self.env.uid:
                raise UserError(_("You cannot delete the expense!"))
        return super(Travel2Application, self).unlink()

    @api.multi
    def copy(self, default=None):
        for expense in self:
            if expense.state not in ['travel_draft']:
                raise UserError(_('不能复制已提交表单'))
        return super(Travel2Application, self).copy()

    @api.multi
    def action_submit_travel(self):  # 营销员提交出差申请
        if self.travel_end_date < self.travel_start_date:
            raise UserError(_("出差结束时间不得小于出差开始时间!"))
        self.write({'state': 'travel_to_audited'})

    @api.multi
    def action_back_to_travel_draft(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hs.expense.v2.travel2.back.wizard',
            'name': '退回向导',
            'view_mode': 'form',
            'context': {
                'travel_id': self.id,
                'default_state': 'travel_draft',
            },
            'target': 'new'
        }

    @api.multi
    def action_first_audited(self):
        employee_id = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)])
        if employee_id != self.first_auditor_id:
            raise UserError(_("您无权审批该申请!"))
        approved_text = self.record_approve()
        self.write({'state': 'first_audited', 'audit_date': datetime.datetime.now(), 'approved_records': approved_text})

    @api.multi
    def action_draft(self):
        employee_id = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)])
        if employee_id != self.second_auditor_id:
            raise UserError(_("您无权审批该申请!"))
        approved_text = self.record_approve()
        self.write({'state': 'draft', 'audit_date': datetime.datetime.now(), 'approved_records': approved_text})

    @api.multi
    def action_back_to_first_audited(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hs.expense.v2.travel2.back.wizard',
            'name': '退回向导',
            'view_mode': 'form',
            'context': {
                'travel_id': self.id,
                'default_state': 'first_audited',
            },
            'target': 'new'
        }

    @api.multi
    def action_submit_expenses(self):  # 营销员提交报销申请
        self.write({'state': 'to_audited'})

    @api.multi
    def action_back_to_draft(self):
        self.audit_cut_amount = 0
        self.audit_amount = 0
        for de in self.sudo().travel_detail_ids:
            de.audit_cut_amount = 0
            de.audit_amount = 0
        # self.write({'state': 'draft'})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hs.expense.v2.travel2.back.wizard',
            'name': '退回向导',
            'view_mode': 'form',
            'context': {
                'travel_id': self.id,
                'default_state': 'draft',
            },
            'target': 'new'
        }

    @api.multi
    def action_audited_expenses(self):
        if self.audit_amount <= 0:
            raise UserError(_("Please enter the correct audit amount!"))
        approved_text = self.record_approve()
        self.write({'state': 'audited', 'audit_date': datetime.datetime.now(), 'approved_records': approved_text})

    @api.multi
    def action_back_to_to_audited(self):
        # self.write({'state': 'to_audited'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hs.expense.v2.travel2.back.wizard',
            'name': '退回向导',
            'view_mode': 'form',
            'context': {
                'travel_id': self.id,
                'default_state': 'to_audited',
            },
            'target': 'new'
        }

    @api.multi
    def action_cashier_expenses(self):
        self.write({'state': 'done', 'audit_date': datetime.datetime.now()})

    def _tranlate_state_name(self, name):
        if name == 'travel_draft':
            return '待提交'
        elif name == 'travel_to_audited':
            return '待审核'
        elif name == 'first_audited':
            return '已审核'
        elif name == 'draft':
            return '已批准'
        elif name == 'to_audited':
            return '已确认'
        elif name == 'audited':
            return '财务审核'
        elif name == 'done':
            return '已支付'

    def _next_state(self, name):
        if name == 'travel_draft':
            return 'travel_to_audited'
        elif name == 'travel_to_audited':
            return 'first_audited'
        elif name == 'first_audited':
            return 'draft'
        elif name == 'draft':
            return 'to_audited'
        elif name == 'to_audited':
            return 'audited'
        elif name == 'audited':
            return 'done'

    def record_approve(self):  # 记录审核过程
        operator = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

        origin_state = self._tranlate_state_name(self.state)
        now_state = self._tranlate_state_name(self._next_state(self.state))

        approved_text = '%s - %s \n%s ---> %s' % \
                        (operator.complete_name if operator.complete_name else 'Administrator',
                         (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
                         origin_state,
                         now_state)
        if self.approved_records:
            approved_text = self.approved_records + '\n\n' + approved_text
        return approved_text

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        domain = self.get_own_forecast_domain(domain)
        return super(Travel2Application, self).search_read(domain, fields, offset, limit, order)

    def get_own_forecast_domain(self, domain=None):
        user_domain = domain or []
        env = self.env
        user_id = env.uid
        if self.user_has_groups('hs_expenses.group_hs_expenses_manager'):
            own_domain = [(1, '=', 1)]
        else:
            employees = env['hs.base.employee'].sudo().search([('user_id', '=', user_id)])
            employee_ids = [employee.id for employee in employees]
            if self.user_has_groups('hs_expenses_v2.group_hs_expenses_travel_application_approver'):
                own_domain = ['|', '|', ('create_uid.id', '=', user_id), '&', ('first_auditor_id', 'in', employee_ids),
                              ('state', 'in', ['travel_to_audited', 'to_audited', 'audited', 'done']),
                              '&', ('second_auditor_id', 'in', employee_ids),
                              ('state', 'in', ['first_audited', 'to_audited', 'audited', 'done'])]
            elif self.user_has_groups('hs_expenses.group_hs_expenses_financial_officer'):
                own_domain = [('state', 'in', ['to_audited', 'audited'])]
            elif self.user_has_groups('hs_expenses.group_hs_expenses_cashier'):
                own_domain = [('state', 'in', ['audited', 'done'])]
            else:
                own_domain = [('create_uid.id', '=', user_id)]
        return user_domain + own_domain

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain = self.get_own_forecast_domain(domain)
        return super(Travel2Application, self.with_context(virtual_id=False)).read_group(domain, fields, groupby,
                                                                                         offset=offset, limit=limit,
                                                                                         orderby=orderby, lazy=lazy)


class Travel2Detail(models.Model):
    _name = 'hs.expense.v2.travel2.detail'
    _description = 'Travel detail'

    @api.depends('to_city')
    def _compute_cost_standard(self):
        travel_standard_model = self.env['hs.expense.travel.standard']
        for detail in self:
            sale_id = detail.travel_application_id.applicant_id
            to_city_level_id = detail.to_city.city_level_id if detail.to_city.city_level_id else \
                self.env['hs.base.city.level'].search([('name', '=', '其他')], limit=1)
            travel_standard = travel_standard_model.search([
                ('employee_level_id', '=', sale_id.employee_level_id.id),
                ('city_level_id', '=', to_city_level_id.id)], limit=1)

            detail.meal_cost_standard = travel_standard.standard_meal_cost
            detail.hotel_cost_standard = travel_standard.standard_hotel_cost
            detail.car_cost_standard = travel_standard.standard_car_cost

    @api.depends('meal_cost', 'hotel_cost', 'car_cost', 'city_car_cost')
    def _compute_total_cost(self):
        for detail in self:
            detail.total_cost = detail.meal_cost + detail.hotel_cost + detail.car_cost + detail.city_car_cost

    @api.onchange('audit_cut_amount')
    def _onchange_audit_cut_amount(self):
        for de in self:
            de.audit_amount = de.total_cost - de.audit_cut_amount
            # de.travel_application_id.audit_cut_amount += de.audit_cut_amount

    @api.onchange('total_cost')
    def _onchange_total_cost(self):
        for de in self:
            de.audit_amount = de.total_cost - de.audit_cut_amount

    start_date = fields.Date(string='Start Date', required=True, default=lambda self: fields.Date.context_today(self))
    end_date = fields.Date(string='End Date', required=True, default=lambda self: fields.Date.context_today(self))
    from_city = fields.Many2one("hs.base.city", string="From City", required=True)
    to_city = fields.Many2one("hs.base.city", string="To City", required=True)
    number_of_days = fields.Integer()
    travel_application_id = fields.Many2one(comodel_name="hs.expense.v2.travel2.application",
                                            string="Travel Application")
    travel_standard_id = fields.Many2one(comodel_name="hs.expense.travel.standard", string="Travel Standard")
    meal_cost = fields.Float("Meal Cost", digits=(16, 2))
    meal_cost_standard = fields.Float("Meal Cost Standard", digits=(16, 2), compute="_compute_cost_standard",
                                      store=True)
    hotel_cost = fields.Float("Hotel Cost", digits=(16, 2))
    hotel_cost_standard = fields.Float("Hotel Cost Standard", digits=(16, 2), compute="_compute_cost_standard",
                                       store=True)
    car_cost = fields.Float("Car Cost", digits=(16, 2))
    car_cost_standard = fields.Float("Car Cost Standard", digits=(16, 2), compute="_compute_cost_standard", store=True)
    city_car_cost = fields.Float("City Car Cost", digits=(16, 2))
    state = fields.Selection([
        ('draft', '已批准'),
        ('to_audited', '已确认'),
        ('audited', '财务审核'),
        ('done', '已支付')
    ], string='Status', copy=False, index=True, readonly=True, default='draft',
        related='travel_application_id.state',
        help="Status of the expense.")

    total_cost = fields.Float("Total Cost", compute="_compute_total_cost", digits=(16, 2))
    audit_cut_amount = fields.Float("Audit Cut Amount", digits=(16, 2))
    audit_cut_remark = fields.Text(string="Audit Cut Remark")
    audit_amount = fields.Float("Audit Amount", digits=(16, 2))
    difference_remark_is_required = fields.Boolean("是否超期", compute="_difference_remark_is_required")
    difference_remark = fields.Text(string="差异备注")

    @api.depends('start_date', 'end_date', 'travel_application_id')
    def _difference_remark_is_required(self):
        for detail in self:
            detail.difference_remark_is_required = (detail.start_date < detail.travel_application_id.travel_start_date) or (
                                                   detail.end_date > detail.travel_application_id.travel_end_date)

    @api.model
    def create(self, values):
        # Add code here
        if values['end_date'] < values['start_date']:
            raise UserError(_("结束日期不得小于开始日期!"))
        return super(Travel2Detail, self).create(values)

    @api.multi
    def write(self, values):
        # Add code here
        return super(Travel2Detail, self).write(values)


class Travel2ApplicationBackWizard(models.TransientModel):
    _name = 'hs.expense.v2.travel2.back.wizard'
    _description = 'Travel application back wizard'

    reason = fields.Text()
    state = fields.Selection([
        ('travel_draft', '待提交'),
        ('travel_to_audited', '待审核'),
        ('first_audited', '已审核'),
        ('draft', '已批准'),
        ('to_audited', '已确认'),
        ('audited', '财务审核'),
        ('done', '已支付')
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='draft',
        help="Status of the expense.")

    def _tranlate_state_name(self, name):
        if name == 'travel_draft':
            return '待提交'
        elif name == 'travel_to_audited':
            return '待审核'
        elif name == 'first_audited':
            return '已审核'
        elif name == 'draft':
            return '已审批'
        elif name == 'to_audited':
            return '已确认'
        elif name == 'audited':
            return '财务审核'
        elif name == 'done':
            return '已支付'

    def save_button(self):
        travel_id = self.env.context.get('travel_id')
        travel = self.env['hs.expense.v2.travel2.application'].browse(int(travel_id))
        operator = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

        origin_state = self._tranlate_state_name(travel.state)
        now_state = self._tranlate_state_name(self.state)

        reason_text = '备注: %s - %s \n%s ---> %s\n%s' % \
                      (operator.complete_name,
                       (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
                       origin_state,
                       now_state,
                       self.reason if self.reason else '无')
        if travel.reason:
            reason_text = travel.reason + '\n\n' + reason_text
        travel.write({'reason': reason_text, 'state': self.state})
        return True


class BatchEndTravelApplicationWizard(models.TransientModel):
    _name = 'hs.expense.v2.batch.end.travel2.wizard'
    _description = 'Batch end travel application wizard'

    application_ids = fields.Many2many(comodel_name='hs.expense.v2.travel2.application',
                                       relation="hs_expense_v2_end_travel2_wizard_entertain_rel",
                                       column1="wizard_id",
                                       column2="application_id",
                                       string='Travel Applications')

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            applications = self.env['hs.expense.v2.travel2.application'].search_read(
                domain=[('id', 'in', active_ids)], fields=['id', 'state'])
            ids = [s['id'] for s in list(filter(lambda s: s['state'] == 'audited', applications))]
            res = {'application_ids': ids}
        return res

    @api.multi
    def batch_end_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        applications = self.env['hs.expense.v2.travel2.application'].search([
            ('id', 'in', active_ids),
            ('state', '=', 'audited')])
        for app in applications:
            app.write({'state': 'done'})
        return {'type': 'ir.actions.act_window_close'}
