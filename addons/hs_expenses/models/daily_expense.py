# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime
import calendar


class BaseApplication(models.AbstractModel):
    _name = 'hs.expense.base.application'
    _rec_name = 'name'
    _description = 'Base Application'

    @api.model
    def _get_default_employee(self):
        return self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    @api.onchange('applicant_id')
    def onchange_applicant_id(self):
        for s in self:
            s.reimbursement_person_id = s.applicant_id
            s.bank_name = s.applicant_id.bank_name
            s.bank_account = s.applicant_id.bank_account

    name = fields.Char(string="Bill Number", require=True)
    applicant_id = fields.Many2one('hs.base.employee', string='Applicant', required=True,
                                   default=_get_default_employee)
    applicant_date = fields.Date(string='Application Date', required=True,
                                 default=lambda self: fields.Date.context_today(self))
    applicant_department_id = fields.Many2one('hs.base.department', related='applicant_id.department_id', store=True)
    cause = fields.Text(string="Cause", required=True)
    application_remark = fields.Text(string="Application Remark")
    sale_area_id = fields.Many2one('hs.sale.area', related='applicant_id.sale_area_id', string='Sale Area', store=True)
    sale_market_id = fields.Many2one('hs.sale.market', related='applicant_id.sale_market_id', string='Sale Market',
                                     store=True)

    reimbursement_person_id = fields.Many2one('hs.base.employee', string="Reimbursement Person", required=True)
    reimbursement_payment_method = fields.Selection(
        [('cash', 'Cash'), ('mt', 'Money Transfer')],
        string='Payment Method', default='mt')
    bank_name = fields.Char(string='Bank Name')
    bank_account = fields.Char(string='Bank Account')
    audit_date = fields.Datetime(string='Audit Date')

    @api.model
    def create(self, values):
        if values.get('travel_detail_ids') is not None:
            for detail in values.get('travel_detail_ids'):
                end = datetime.datetime.strptime(detail[2]['end_date'], '%Y-%m-%d').date()
                today = datetime.datetime.today()
                if today.month != end.month:
                    raise UserError(_("The end date of the trip must be in the current month."))
        return super(BaseApplication, self).create(values)


class TravelDetail(models.Model):
    _name = 'hs.expense.travel.detail'
    _description = 'Travel detail'

    # @api.onchange('to_city')
    @api.depends('to_city')
    def _compute_cost_standard(self):
        travel_standard_model = self.env['hs.expense.travel.standard']
        for detail in self:
            sale_id = detail.travel_application_id.applicant_id
            to_city_level_id = detail.to_city.city_level_id if detail.to_city.city_level_id else self.env['hs.base.city.level'].search([('name', '=', '其他')], limit=1)
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

    start_date = fields.Date(string='Start Date', required=True,
                                 default=lambda self: fields.Date.context_today(self))
    end_date = fields.Date(string='End Date', required=True,
                             default=lambda self: fields.Date.context_today(self))
    from_city = fields.Many2one("hs.base.city", string="From City", required=True)
    to_city = fields.Many2one("hs.base.city", string="To City", required=True)
    number_of_days = fields.Integer()
    travel_application_id = fields.Many2one(comodel_name="hs.expense.travel.application", string="Travel Application")
    travel_standard_id = fields.Many2one(comodel_name="hs.expense.travel.standard", string="Travel Standard")
    meal_cost = fields.Float("Meal Cost", digits=(16, 2))
    meal_cost_standard = fields.Float("Meal Cost Standard", digits=(16, 2), compute="_compute_cost_standard", store=True)
    hotel_cost = fields.Float("Hotel Cost", digits=(16, 2))
    hotel_cost_standard = fields.Float("Hotel Cost Standard", digits=(16, 2), compute="_compute_cost_standard", store=True)
    car_cost = fields.Float("Car Cost", digits=(16, 2))
    car_cost_standard = fields.Float("Car Cost Standard", digits=(16, 2), compute="_compute_cost_standard", store=True)
    city_car_cost = fields.Float("City Car Cost", digits=(16, 2))
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('to_approved', 'To Approved'),
        ('to_audited', 'To Audited'),
        ('audited', 'Audited'),
        ('done', 'Paid')
    ], string='Status', copy=False, index=True, readonly=True, default='draft',
        related='travel_application_id.state',
        help="Status of the expense.")

    total_cost = fields.Float("Total Cost", compute="_compute_total_cost", digits=(16, 2))

    @api.model
    def create(self, values):
        # Add code here
        return super(TravelDetail, self).create(values)

    @api.multi
    def write(self, values):
        # Add code here
        return super(TravelDetail, self).write(values)


class TravelApplication(models.Model):
    _name = 'hs.expense.travel.application'
    _inherit = 'hs.expense.base.application'
    _description = 'Travel expenses reimbursement form'
    _order = 'applicant_date desc, id desc'

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

    @api.depends('month_application_id')
    def _compute_state(self):
        for travel in self:
            travel.state = travel.month_application_id.state

    def _compute_current_user_is_financial(self):
        self.current_user_is_financial = self.user_has_groups('hs_expenses.group_hs_expenses_financial_officer')

    @api.onchange('audit_cut_amount')
    def _onchange_audit_cut_amount(self):
        for travel in self:
            travel.audit_amount = travel.total_cost - self.audit_cut_amount

    destination_city = fields.Many2one("hs.base.city", string="Destination City", required=True)
    travel_detail_ids = fields.One2many('hs.expense.travel.detail', 'travel_application_id', string='Travel Details')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('to_approved', 'To Approved'),
        ('to_audited', 'To Audited'),
        ('audited', 'Audited'),
        ('done', 'Paid')
    ], string='Status', copy=False, index=True, readonly=True, default='draft',
        # compute="_compute_state",
        related='month_application_id.state',
        help="Status of the expense.")

    reimbursement_remark = fields.Text(string="Reimbursement Remark")
    month_application_id = fields.Many2one(comodel_name="hs.expense.month.application", string="Month Application",
                                           required=False, )
    meal_total_cost = fields.Float("Total Meal Cost", compute="_compute_meal_total_cost", digits=(16, 2))
    hotel_total_cost = fields.Float("Total Hotel Cost", compute="_compute_hotel_total_cost", digits=(16, 2))
    car_total_cost = fields.Float("Total Car Cost", compute="_compute_car_total_cost", digits=(16, 2))
    city_car_total_cost = fields.Float("Total City Car Cost", compute="_compute_city_car_total_cost", digits=(16, 2))
    total_cost = fields.Float("Total Cost", compute="_compute_total_cost", digits=(16, 2))
    audit_amount = fields.Float("Audit Amount", digits=(16, 2))
    audit_cut_amount = fields.Float("Audit Cut Amount", digits=(16, 2))
    audit_remark = fields.Text(string="Audit Remark")
    current_user_is_financial = fields.Boolean(compute="_compute_current_user_is_financial")
    is_exceed = fields.Boolean(related='month_application_id.is_exceed')

    @api.model
    def create(self, values):
        if values.get('name') is None or values.get('name') is False:
            name = self.env['ir.sequence'].next_by_code('hs.expense.travel.application.no')
            if not name:
                self.env['ir.sequence'].sudo().create({
                    'number_next': 1,
                    'number_increment': 1,
                    'padding': 8,
                    'prefix': 'TA',
                    'name': 'Travel Application NO.',
                    'code': 'hs.expense.travel.application.no',
                })
                name = self.env['ir.sequence'].next_by_code('hs.expense.travel.application.no')
            values['name'] = name

        if values.get('travel_detail_ids') is not None:
            for detail in values.get('travel_detail_ids'):
                end = datetime.datetime.strptime(detail[2]['end_date'], '%Y-%m-%d').date()
                today = datetime.datetime.today()
                if today.month != end.month:
                    raise UserError(_("The end date of the trip must be in the current month."))
        return super(TravelApplication, self).create(values)

    @api.multi
    def write(self, values):
        # Add code here
        return super(TravelApplication, self).write(values)

    @api.multi
    def unlink(self):
        for expense in self:
            if expense.state not in ['draft']:
                raise UserError(_('You cannot delete a posted or approved expense.'))
            if expense.create_uid.id != self.env.uid:
                raise UserError(_("You cannot delete the expense!"))
        return super(TravelApplication, self).unlink()


class OrdinaryApplication(models.Model):
    _name = 'hs.expense.ordinary.application'
    _inherit = 'hs.expense.base.application'
    _description = 'Ordinary application and reimbursement form'

    @api.depends('month_application_id')
    def _compute_state(self):
        for travel in self:
            travel.state = travel.month_application_id.state

    def _compute_current_user_is_financial(self):
        self.current_user_is_financial = self.user_has_groups('hs_expenses.group_hs_expenses_financial_officer')

    applicant_amount = fields.Float("Applicant Amount", required=True, max=2000, digits=(16, 2))

    # reimbursement_amount = fields.Float(
    #     "Reimbursement Amount",
    #     required=True,
    #     digits=(16, 2))
    reimbursement_remark = fields.Text(string="Reimbursement Remark")
    audit_amount = fields.Float("Audit Amount", digits=(16, 2))
    current_user_is_financial = fields.Boolean(compute="_compute_current_user_is_financial")
    month_application_id = fields.Many2one(comodel_name="hs.expense.month.application", string="Month Application",
                                           required=False, )
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('to_approved', 'To Approved'),
        ('to_audited', 'To Audited'),
        ('audited', 'Audited'),
        ('done', 'Paid')
    ], string='Status', copy=False, index=True, readonly=True, default='draft',
        related='month_application_id.state',
        # compute='_compute_state',
        help="Status of the expense.")
    is_exceed = fields.Boolean(related='month_application_id.is_exceed')
    happen_date = fields.Date(string='Happen Date', required=True,
                                 default=lambda self: fields.Date.context_today(self))

    @api.model
    def create(self, values):
        if values.get('name') is None or values.get('name') is False:
            name = self.env['ir.sequence'].next_by_code('hs.expense.ordinary.application.no')
            if not name:
                self.env['ir.sequence'].sudo().create({
                    'number_next': 1,
                    'number_increment': 1,
                    'padding': 8,
                    'prefix': 'OA',
                    'name': 'Ordinary Application NO.',
                    'code': 'hs.expense.ordinary.application.no',
                })
                name = self.env['ir.sequence'].next_by_code('hs.expense.ordinary.application.no')
            values['name'] = name
        if float(values.get('applicant_amount')) > 2000:
            raise UserError(_('The application amount shall not be more than 2000.'))
        return super(OrdinaryApplication, self).create(values)

    @api.multi
    def write(self, vals):
        if self.applicant_amount > 2000:
            raise UserError(_('The application amount shall not be more than 2000.'))
        return super(OrdinaryApplication, self).write(vals)

    @api.multi
    def unlink(self):
        for expense in self:
            if expense.state not in ['draft']:
                raise UserError(_('You cannot delete a posted or approved expense.'))
            if expense.create_uid.id != self.env.uid:
                raise UserError(_("You cannot delete the expense!"))
        return super(OrdinaryApplication, self).unlink()


class MonthApplication(models.Model):
    _name = 'hs.expense.month.application'
    _description = 'Monthly routine summary form'

    @api.model
    def _get_default_employee(self):
        return self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    @api.depends('total_cost', 'seller_id.current_month_quota_remained')
    def _compute_is_exceed(self):
        self.is_exceed = self.total_cost > self.seller_id.current_month_quota_remained

    @api.depends('travel_application_ids')
    def _compute_meal_total_cost(self):
        for app in self:
            if app.travel_application_ids is not None or app.travel_application_ids is not False:
                for travel in app.travel_application_ids:
                    app.meal_total_cost += travel.meal_total_cost

    @api.depends('travel_application_ids')
    def _compute_hotel_total_cost(self):
        for app in self:
            if app.travel_application_ids is not None or app.travel_application_ids is not False:
                for travel in app.travel_application_ids:
                    app.hotel_total_cost += travel.hotel_total_cost

    @api.depends('travel_application_ids')
    def _compute_car_total_cost(self):
        for app in self:
            if app.travel_application_ids is not None or app.travel_application_ids is not False:
                for travel in app.travel_application_ids:
                    app.car_total_cost += travel.car_total_cost

    @api.depends('travel_application_ids')
    def _compute_city_car_total_cost(self):
        for app in self:
            if app.travel_application_ids is not None or app.travel_application_ids is not False:
                for travel in app.travel_application_ids:
                    app.city_car_total_cost += travel.city_car_total_cost

    @api.depends('ordinary_application_ids')
    def _compute_total_ordinary_applicant_amount(self):
        for app in self:
            if app.ordinary_application_ids is not None or app.ordinary_application_ids is not False:
                for ordinary in app.ordinary_application_ids:
                    app.total_ordinary_applicant_amount += ordinary.applicant_amount

    @api.depends('travel_application_ids')
    def _compute_total_travel_applicant_amount(self):
        for app in self:
            if app.travel_application_ids is not None or app.travel_application_ids is not False:
                for travel in app.travel_application_ids:
                    app.total_travel_applicant_amount += travel.total_cost

    @api.depends('total_cost')
    def _compute_total_cost(self):
        for app in self:
            total_travel_cost = 0
            total_ordinary_cost = 0
            if app.travel_application_ids is not None or app.travel_application_ids is not False:
                for travel in app.travel_application_ids:
                    total_travel_cost += travel.total_cost
            if app.ordinary_application_ids is not None or app.ordinary_application_ids is not False:
                for ordinary in app.ordinary_application_ids:
                    total_ordinary_cost += ordinary.applicant_amount
            app.total_cost = total_ordinary_cost + total_travel_cost

    # @api.depends('travel_application_ids', 'ordinary_application_ids')
    @api.onchange('travel_application_ids', 'ordinary_application_ids')
    def _compute_audit_amount(self):
        for app in self:
            app.audit_amount = 0
            if app.travel_application_ids is not None or app.travel_application_ids is not False:
                for travel in app.travel_application_ids:
                    app.audit_amount += travel.audit_amount
            if app.ordinary_application_ids is not None or app.ordinary_application_ids is not False:
                for ordinary in app.ordinary_application_ids:
                    app.audit_amount += ordinary.audit_amount

    @api.onchange('travel_application_ids')
    def _compute_total_travel_audit_amount(self):
        for app in self:
            app.total_travel_audit_amount = 0
            if app.travel_application_ids is not None or app.travel_application_ids is not False:
                for travel in app.travel_application_ids:
                    app.total_travel_audit_amount += travel.audit_amount

    @api.onchange('ordinary_application_ids')
    def _compute_total_ordinary_audit_amount(self):
        for app in self:
            app.total_ordinary_audit_amount = 0
            if app.ordinary_application_ids is not None or app.ordinary_application_ids is not False:
                for ordinary in app.ordinary_application_ids:
                    app.total_ordinary_audit_amount += ordinary.audit_amount

    def _compute_current_user_is_financial(self):
        if self.user_has_groups('hs_expenses.group_hs_expenses_financial_officer'):
            self.current_user_is_financial = True
        else:
            self.current_user_is_financial = False

    @api.onchange('ordinary_application_ids')
    def _onchange_ordinary_application_ids(self):
        if self.ordinary_application_ids is not None and self.ordinary_application_ids is not False:
            for ord in self.ordinary_application_ids:
                if ord.applicant_amount > 2000:
                    raise UserError(_('The application amount shall not be more than 2000.'))

    @api.one
    @api.depends('countersign_ids')
    def _compute_current_sign_completed(self):
        self.current_sign_completed = False
        current_employee = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        for sign in self.countersign_ids:
            if sign.employee_id.id == current_employee.id:
                self.current_sign_completed = sign.is_approved

    name = fields.Char(string="Bill Number", require=True)
    seller_id = fields.Many2one('hs.base.employee', string='Applicant', required=True,
                                default=_get_default_employee)
    bill_date = fields.Date(string='Bill Date', required=True,
                            default=lambda self: fields.Date.context_today(self))

    travel_application_ids = fields.One2many(comodel_name="hs.expense.travel.application",
                                             inverse_name="month_application_id",
                                             string="Travel Application",
                                             required=False, )
    ordinary_application_ids = fields.One2many(comodel_name="hs.expense.ordinary.application",
                                               inverse_name="month_application_id",
                                               string="Ordinary Application",
                                               required=False, )
    is_exceed = fields.Boolean(compute="_compute_is_exceed")
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('reported', 'Submitted'),
        ('to_approved', 'To Approved'),
        ('to_audited', 'To Audited'),
        ('audited', 'Audited'),
        ('countersign', 'Countersign'),
        ('done', 'Paid')
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='draft',
        help="Status of the expense.")

    meal_total_cost = fields.Float("Total Meal Cost", compute="_compute_meal_total_cost", digits=(16, 2))
    hotel_total_cost = fields.Float("Total Hotel Cost", compute="_compute_hotel_total_cost", digits=(16, 2))
    car_total_cost = fields.Float("Total Car Cost", compute="_compute_car_total_cost", digits=(16, 2))
    city_car_total_cost = fields.Float("City Total Car Cost", compute="_compute_city_car_total_cost", digits=(16, 2))
    total_ordinary_applicant_amount = fields.Float("Total Ordinary Applicant Amount",
                                                   compute="_compute_total_ordinary_applicant_amount", digits=(16, 2))
    total_travel_applicant_amount = fields.Float("Total Travel Applicant Amount",
                                                   compute="_compute_total_travel_applicant_amount", digits=(16, 2))
    total_cost = fields.Float("Total Cost", compute="_compute_total_cost", digits=(16, 2))
    current_month_quota = fields.Float("Current Month Quota", related='seller_id.current_month_quota')
    # audit_amount = fields.Float("Audit Amount", digits=(16, 2), readonly=lambda self: self._set_audit_amount_readonly())
    audit_amount = fields.Float("Audit Amount", digits=(16, 2), compute="_compute_audit_amount")
    total_travel_audit_amount = fields.Float("Total Travel Audit Amount", digits=(16, 2),
                                             compute="_compute_total_travel_audit_amount")
    total_ordinary_audit_amount = fields.Float("Total Ordinary Audit Amount", digits=(16, 2),
                                             compute="_compute_total_ordinary_audit_amount")
    current_user_is_financial = fields.Boolean(compute="_compute_current_user_is_financial")
    audit_date = fields.Datetime(string='Audit Date')

    complete_countersign = fields.Boolean(default=False)
    countersign_ids = fields.One2many('hs.expense.countersign.month', 'expense_id', string='Countersign', readonly=True)
    current_sign_completed = fields.Boolean(compute='_compute_current_sign_completed')

    @api.model
    def create(self, values):
        if values.get('name') is None or values.get('name') is False:
            name = self.env['ir.sequence'].next_by_code('hs.expense.month.application.no')
            if not name:
                self.env['ir.sequence'].sudo().create({
                    'number_next': 1,
                    'number_increment': 1,
                    'padding': 8,
                    'prefix': 'MA',
                    'name': 'Month Application NO.',
                    'code': 'hs.expense.month.application.no',
                })
                name = self.env['ir.sequence'].next_by_code('hs.expense.month.application.no')
            values['name'] = name
        return super(MonthApplication, self).create(values)

    @api.multi
    def unlink(self):
        for expense in self:
            if expense.state not in ['draft']:
                raise UserError(_('You cannot delete a posted or approved expense.'))
            if expense.create_uid.id != self.env.uid:
                raise UserError(_("You cannot delete the expense!"))
        return super(MonthApplication, self).unlink()

    @api.multi
    def action_submit_expenses(self): # 营销员提交草稿到报告状态
        today = fields.Date.today()
        # day = today.day
        # month = today.month
        bill_date = self.bill_date

        days_nums_of_bill_date = calendar.monthrange(bill_date.year, bill_date.month)[1]
        first_day_of_bill_date = datetime.date(bill_date.year, bill_date.month, 1)
        seven_day_of_next_bill_date = first_day_of_bill_date + datetime.timedelta(days= days_nums_of_bill_date + 6)

        if today.year == seven_day_of_next_bill_date.year and \
                today.month == seven_day_of_next_bill_date.month and \
                today.day <= seven_day_of_next_bill_date.day:
            pass
        else:
            raise UserError(_("Please submit by the 7th of the next month of bill date."))

        # if month - bill_date.month == 1 and today.day <= 7:
        #     pass
        # else:
        #     raise UserError(_("Please submit by the 7th of the next month of bill date."))

        # 判断额度是否足够
        current_month_quota_remained = self.seller_id.current_month_quota_remained
        # if self.total_cost > current_month_quota_remained:
            # 弹出超额提示，点确定进入会签，点取消自行删除部分费用
            # 当月您的额度已经不足
            # 您可以点“否”返回表单删除超出部分费用再提交
            # 您也可以点“是”通过会签流程继续提交
            # msg = _('Your quota is already insufficient in the month.') + '\r\n' + \
            #       _('You can click "No" to return to the form to delete the excess fee and submit') + '\r\n' + \
            #       _('You can also click "Yes" to continue submitting through the signing process.')
            # return {
            #     'type': 'ir.actions.act_window',
            #     'res_model': 'hs.expense.confirm.dialog',
            #     'name': _('Confirm'),
            #     'view_mode': 'form',
            #     'context': {
            #         'default_message': msg
            #     },
            #     'target': 'new'
            # }
            #20190528 改为由姜烨一个人审批
            # pass

        msg = ""
        if self.total_cost > current_month_quota_remained:
            self.is_exceed = True
            msg = _('Your monthly quota is insufficient. '
                    'Click Confirm to submit it to relevant personnel for review.') # 您当月额度已经不足，点击确定提交给相关人员审核
        else:
            self.is_exceed = False
            msg = _('Your monthly quota is sufficient. '
                    'Click Confirm to submit to the financial staff for review.') # 您当月额度足够，点击确定提交给财务人员审核
        if not self.is_exceed:
            self.write({'state': 'reported'})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hs.expense.confirm.dialog',
            'name': _('Confirm'),
            'view_mode': 'form',
            'context': {
                'default_month_application_id': self.id,
                'default_message': msg,
                'default_is_exceed': self.is_exceed,
            },
            'target': 'new'
        }

    # todo: 增加用户组权限判断
    @api.multi
    def action_reported_to_approve(self):
        # 从报告状态提交到待批准状态，累计已使用额度
        self.sudo().seller_id.current_month_quota_used += self.total_cost
        self.write({'state': 'to_approved'})

    @api.multi
    def action_approve_to_audit(self): # 姜烨从待批准状态转待审核状态
        self.write({'state': 'to_audited'})

    @api.multi
    def action_back_to_reported(self): # 姜烨退回从待确认到报告状态
        # 返回报告状态，只能删除子单据不能修改金额
        # 退回报告状态，减去已使用额度
        self.sudo().seller_id.current_month_quota_used -= self.total_cost
        self.write({'state': 'reported'})

    @api.multi
    def action_audit_expenses(self):  # 财务审核完成，提交给出纳
        self.sudo().seller_id.current_month_quota_used = 0
        if self.travel_application_ids is not None or self.travel_application_ids is not False:
            for travel in self.travel_application_ids:
                travel.audit_date = datetime.datetime.now()

        if self.ordinary_application_ids is not None or self.ordinary_application_ids is not False:
            for ordinary in self.ordinary_application_ids:
                ordinary.audit_date = datetime.datetime.now()

        if self.audit_amount >= 5000:
            group_id = self.env.ref('hs_expenses.group_hs_expenses_leader').id
            leaders = self.env['res.users'].search([('groups_id', '=', group_id)])
            countersign = self.env['hs.expense.countersign.month']

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

            self.write({'state': 'countersign', 'audit_date': datetime.datetime.now()})
        else:
            self.write({'state': 'audited', 'audit_date': datetime.datetime.now()})

    @api.multi
    def action_back_to_to_audited(self):  # 出纳退回给财务审核
        self.write({'state': 'to_audited'})

    @api.multi
    def action_cashier_expenses(self):  # 出纳放款结束流程
        self.write({'state': 'done'})

    @api.multi
    def function_countersign_expenses(self): # 高层会签
        employee = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        if employee and employee is not None:
            expense_id = self
            countersign = self.env['hs.expense.countersign.month'].search(
                [('employee_id', '=', employee.id), ('expense_id', '=', expense_id.id)], limit=1)
            if countersign and countersign is not None:
                countersign.write({'is_approved': True})
            else:
                raise UserError(_("Some errors have occurred in the system!"))

            if not any(sign.is_approved is False
                       for sign in self.env['hs.expense.countersign.month'].search([('expense_id', '=', expense_id.id)])):
                self.write({'complete_countersign': True, 'state': 'audited'})
                # self.action_done_expenses()
        return True


class CounterSignMonth(models.Model):
    _name = 'hs.expense.countersign.month'
    _description = 'Month Countersign'

    employee_id = fields.Many2one('hs.base.employee', string='Employee', required=True)
    expense_id = fields.Many2one('hs.expense.month.application', string='Month Application')
    is_approved = fields.Boolean(default=False)


class ExpenseConfirmDialog(models.TransientModel): # 营销员点确认从报告状态转成确认状态/待审核状态
    _name = 'hs.expense.confirm.dialog'

    month_application_id = fields.Many2one(comodel_name="hs.expense.month.application", required=True, )
    message = fields.Text(readonly=True)
    is_exceed = fields.Boolean()

    def yes(self):
        if self.is_exceed:
            self.month_application_id.state = 'to_approved'
        else:
            self.month_application_id.state = 'to_audited'
        self.sudo().month_application_id.seller_id.current_month_quota_used += self.month_application_id.total_cost


class BatchEndMonthApplicationWizard(models.TransientModel):
    _name = 'month.batch.end.wizard'
    _description = 'Batch end application wizard'

    application_ids = fields.Many2many('hs.expense.month.application', string='Month Applications')

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            applications = self.env['hs.expense.month.application'].search_read(
                domain=[('id', 'in', active_ids)], fields=['id', 'state'])
            ids = [s['id'] for s in list(filter(lambda s: s['state'] == 'audited', applications))]
            res = {'application_ids': ids}
        return res

    @api.multi
    def batch_end_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        if active_ids:
            applications = self.env['hs.expense.month.application'].search([
                ('id', 'in', active_ids),
                ('state', '=', 'audited')])
            applications.write({'state': 'done'})
        return {'type': 'ir.actions.act_window_close'}

