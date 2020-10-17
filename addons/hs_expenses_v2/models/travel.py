# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime
import calendar


class BaseApplication(models.AbstractModel):
    _name = 'hs.expense.v2.base.application'
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

    # driver_type = fields.Selection([('BD - VISIT', 'Business Development - Visit'),
    #                                 ('BD - ENTERTAIN', 'Business Development - Entertain'),
    #                                 ('OP', 'Order Processing'),
    #                                 ('QP', 'Quality Processing'),
    #                                 ('PS', 'Project Support'),
    #                                 ('TM', 'Tracking Money'),
    #                                 ('CF', 'Conference Forum'),], string="Driver Type", copy=False, index=True,
    #                                required=True)
    driver_type_id = fields.Many2one("hs.base.driver.type", string="Driver Type", required=True)
    customer_name = fields.Char(string="Customer Name", required=True)
    project_id = fields.Many2one('hs.base.project', string='Project')

    @api.model
    def create(self, values):
        # if values.get('travel_detail_ids') is not None:
        #     for detail in values.get('travel_detail_ids'):
        #         end = datetime.datetime.strptime(detail[2]['end_date'], '%Y-%m-%d').date()
        #         today = datetime.datetime.today()
        #         if today.month != end.month:
        #             raise UserError(_("The end date of the trip must be in the current month."))
        return super(BaseApplication, self).create(values)


class TravelDetail(models.Model):
    _name = 'hs.expense.v2.travel.detail'
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

    start_date = fields.Date(string='Start Date', required=True, default=lambda self: fields.Date.context_today(self))
    end_date = fields.Date(string='End Date', required=True, default=lambda self: fields.Date.context_today(self))
    from_city = fields.Many2one("hs.base.city", string="From City", required=True)
    to_city = fields.Many2one("hs.base.city", string="To City", required=True)
    number_of_days = fields.Integer()
    travel_application_id = fields.Many2one(comodel_name="hs.expense.v2.travel.application", string="Travel Application")
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
        ('to_audited', 'To Audited'),
        ('audited', 'Audited'),
        ('done', 'Paid')
    ], string='Status', copy=False, index=True, readonly=True, default='draft',
        related='travel_application_id.state',
        help="Status of the expense.")

    total_cost = fields.Float("Total Cost", compute="_compute_total_cost", digits=(16, 2))
    audit_cut_amount = fields.Float("Audit Cut Amount", digits=(16, 2))
    audit_cut_remark = fields.Text(string="Audit Cut Remark")
    audit_amount = fields.Float("Audit Amount", digits=(16, 2))

    @api.model
    def create(self, values):
        # Add code here
        return super(TravelDetail, self).create(values)

    @api.multi
    def write(self, values):
        # Add code here
        return super(TravelDetail, self).write(values)


class TravelApplication(models.Model):
    _name = 'hs.expense.v2.travel.application'
    _inherit = 'hs.expense.v2.base.application'
    _description = 'Travel expenses reimbursement form'
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
            travel.audit_amount = travel.total_cost - self.audit_cut_amount

    destination_city = fields.Many2one("hs.base.city", string="Destination City", required=True)
    travel_detail_ids = fields.One2many('hs.expense.v2.travel.detail', 'travel_application_id', string='Travel Details')
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('to_audited', 'To Audited'),
        ('audited', 'Audited'),
        ('done', 'Paid')
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='draft',
        help="Status of the expense.")

    reimbursement_remark = fields.Text(string="Reimbursement Remark")

    meal_total_cost = fields.Float("Total Meal Cost", compute="_compute_meal_total_cost", digits=(16, 2))
    hotel_total_cost = fields.Float("Total Hotel Cost", compute="_compute_hotel_total_cost", digits=(16, 2))
    car_total_cost = fields.Float("Total Car Cost", compute="_compute_car_total_cost", digits=(16, 2))
    city_car_total_cost = fields.Float("Total City Car Cost", compute="_compute_city_car_total_cost", digits=(16, 2))
    total_cost = fields.Float("Total Cost", compute="_compute_total_cost", digits=(16, 2))

    audit_amount = fields.Float("Audit Amount", digits=(16, 2), compute="_compute_audit_amount")
    audit_cut_amount = fields.Float("Audit Cut Amount", digits=(16, 2), compute="_compute_audit_amount")
    audit_remark = fields.Text(string="Audit Remark")
    current_user_is_financial = fields.Boolean(compute="_compute_current_user_is_financial")
    # group_text = fields.Html(compute="_compute_group_text")

    @api.multi
    @api.depends('travel_detail_ids')
    # TODO: update template
    def _compute_group_text(self):
        for rec in self:
            text = ''
            if rec.travel_detail_ids:
                text = '<table class="o_list_view table table-sm table-hover table-striped o_list_view_ungrouped">' \
                       '<tfoot>' \
                       '<tr class="o_data_row">' \
                       '<td class="o_data_cell o_required_modifier" width="11%%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>' \
                       '<td class="o_data_cell o_required_modifier" width="11%%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>' \
                       '<td class="o_data_cell o_required_modifier" width="11%%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>' \
                       '<td class="o_data_cell o_required_modifier" width="11%%">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</td>' \
                       '<td class="o_data_cell o_list_number" width="11%%" style="text-align:right;">%s</td>' \
                       '<td class="o_data_cell o_list_number" width="11%%" style="text-align:right;">%s</td>' \
                       '<td class="o_data_cell o_list_number" width="11%%" style="text-align:right;">%s</td>' \
                       '<td class="o_data_cell o_list_number" width="11%%" style="text-align:right;">%s</td>' \
                       '<td class="o_data_cell o_list_number" width="11%%" style="text-align:right;">%s</td>' \
                       '</tr></tfoot></table>' % ('%.2f' % rec.car_total_cost,
                                                  '%.2f' % rec.meal_total_cost,
                                                  '%.2f' % rec.hotel_total_cost,
                                                  '%.2f' % rec.city_car_total_cost,
                                                  '%.2f' % rec.total_cost)
            rec.group_text = text

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
                    'code': 'hs.expense.v2.travel.app.no',
                })
                name = self.env['ir.sequence'].next_by_code('hs.expense.v2.travel.app.no')
            values['name'] = name

        # if values.get('travel_detail_ids') is not None:
        #     for detail in values.get('travel_detail_ids'):
        #         end = datetime.datetime.strptime(detail[2]['end_date'], '%Y-%m-%d').date()
        #         today = datetime.datetime.today()
        #         if today.month != end.month:
        #             raise UserError(_("The end date of the trip must be in the current month."))
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

    @api.multi
    def action_submit_expenses(self):  # 营销员提交
        self.write({'state': 'to_audited'})

    @api.multi
    def action_back_to_draft(self):
        self.audit_cut_amount = 0
        self.audit_amount = 0
        for de in self.sudo().travel_detail_ids:
            de.audit_cut_amount = 0
            de.audit_amount = 0
        self.write({'state': 'draft'})

    @api.multi
    def action_audit_expenses(self):
        if self.audit_amount <= 0:
            raise UserError(_("Please enter the correct audit amount!"))
        self.write({'state': 'audited'})

    @api.multi
    def action_back_to_to_audited(self):
        self.write({'state': 'to_audited'})

    @api.multi
    def action_cashier_expenses(self):
        self.write({'state': 'done'})


class BatchEndTravelApplicationWizard(models.TransientModel):
    _name = 'hs.expense.v2.batch.end.travel.wizard'
    _description = 'Batch end travel application wizard'

    application_ids = fields.Many2many(comodel_name='hs.expense.v2.travel.application',
                                       relation="hs_expense_v2_end_travel_wizard_entertain_rel",
                                       column1="wizard_id",
                                       column2="application_id",
                                       string='Travel Applications')

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            applications = self.env['hs.expense.v2.travel.application'].search_read(
                domain=[('id', 'in', active_ids)], fields=['id', 'state'])
            ids = [s['id'] for s in list(filter(lambda s: s['state'] == 'audited', applications))]
            res = {'application_ids': ids}
        return res

    @api.multi
    def batch_end_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        applications = self.env['hs.expense.v2.travel.application'].search([
            ('id', 'in', active_ids),
            ('state', '=', 'audited')])
        applications.write({'state': 'done'})
        return {'type': 'ir.actions.act_window_close'}