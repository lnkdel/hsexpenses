# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_resource
import pytz
import base64

DEPARTMENT_COMPLETE_NAME_SEPARATOR = ' / '
_logger = logging.getLogger(__name__)


class EmployeeTag(models.Model):
    _name = "hs.base.employee.tag"
    _description = "Employee Tag"
    _order = 'sequence, name'

    name = fields.Char(string="Name", required=True)
    color = fields.Integer(string='Color')
    employee_ids = fields.Many2many('hs.base.employee', 'hs_base_employee_tag_rel', 'tag_id', 'employee_id',
                                    string='Employees')
    note = fields.Text('Note')
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Tag name already exists!'),
    ]


class Employee(models.Model):
    _name = "hs.base.employee"
    _description = "Employee"
    _rec_name = 'complete_name'
    _order = 'employee_no'
    _mail_post_access = 'read'

    name = fields.Char(required=True, string='Name')
    employee_no = fields.Char(required=True, string='Employee No.')
    complete_name = fields.Char(compute='_compute_complete_name', string='Complete Name', store=True)
    company_id = fields.Many2one('res.company', string='Company', index=True,
                                 default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', string='User')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])
    department_id = fields.Many2one('hs.base.department', string='Department', ondelete='restrict')
    other_department_ids = fields.Many2many('hs.base.department', string='Other Departments')
    rfid = fields.Char(string='RFID')
    active = fields.Boolean(string='Active', default=True)
    phone = fields.Char('Phone')
    mobile_phone = fields.Char('Mobile Phone')
    email = fields.Char('Email')
    wechat_account = fields.Char('WeChat Account', index=True)
    note = fields.Text('Note')
    parent_id = fields.Many2one('hs.base.employee', string='Manager')
    child_ids = fields.One2many('hs.base.employee', 'parent_id', string='Subordinates')
    tag_ids = fields.Many2many('hs.base.employee.tag', 'hs_base_employee_tag_rel', 'employee_id', 'tag_id',
                               string='Tags')
    login = fields.Char(related='user_id.login', readonly=True)
    last_login = fields.Datetime(related='user_id.login_date', string='Latest Connection', readonly=True)

    @api.model
    def _default_image(self):
        image_path = get_module_resource('hs_base', 'static/src/img', 'default_employee_image.png')
        return tools.image_resize_image_big(base64.b64encode(open(image_path, 'rb').read()))

    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary("Photo", default=_default_image, attachment=True)
    image_medium = fields.Binary("Medium-sized photo", attachment=True)
    image_small = fields.Binary("Small-sized photo", attachment=True)

    _sql_constraints = [
        ('employee_no_uniq', 'unique(employee_no)', 'Employee No. already exists!'),
        ('wechat_account_uniq', 'unique(wechat_account)', 'WeChat Account already exists!'),
    ]

    @api.constrains('parent_id')
    def _check_parent_id(self):
        for employee in self:
            if not employee._check_recursion():
                raise ValidationError(_('Error! Cannot create recursive hierarchy of Employee(s).'))

    @api.one
    @api.depends('name', 'employee_no')
    def _compute_complete_name(self):
        names = [self.employee_no, self.name]
        self.complete_name = ' / '.join(filter(None, names))

    @api.model
    def create(self, vals):
        tools.image_resize_images(vals)
        return super(Employee, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        return super(Employee, self).write(vals)


class Department(models.Model):
    _name = "hs.base.department"
    _rec_name = 'complete_name'
    _description = "Department"
    _order = 'sequence, name'

    name = fields.Char('Department Name', required=True)
    complete_name = fields.Char(compute='_compute_complete_name', string='Complete Name', store=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', index=True,
                                 default=lambda self: self.env.user.company_id)
    parent_id = fields.Many2one('hs.base.department', string='Parent Department', index=True)
    child_ids = fields.One2many('hs.base.department', 'parent_id', string='Child Departments')
    manager_id = fields.Many2one('hs.base.employee', string='Manager')
    member_ids = fields.One2many('hs.base.employee', 'department_id', string='Members', readonly=True)
    note = fields.Text('Note')
    color = fields.Integer('Color')
    sequence = fields.Integer(string="Sequence", default=10)

    @api.multi
    @api.depends('name', 'parent_id')
    def _compute_complete_name(self):
        for record in self:
            if record.name:
                name = record.name
                current = record
                while current.parent_id:
                    current = current.parent_id
                    name = DEPARTMENT_COMPLETE_NAME_SEPARATOR.join((current.name, name))
                record.complete_name = name
            else:
                record.complete_name = False

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create recursive departments.'))

    @api.multi
    def write(self, vals):
        result = super(Department, self).write(vals)
        if not self.env.context.get('set_sub_complete_names'):
            if 'parent_id' in vals or 'name' in vals:
                self = self.with_context(set_sub_complete_names=True)
                for record in self:
                    self._set_sub_complete_names(record, DEPARTMENT_COMPLETE_NAME_SEPARATOR)
        return result

    def _set_sub_complete_names(self, record, separator):
        for child in record.child_ids:
            child.complete_name = separator.join((record.complete_name, child.name))
            self._set_sub_complete_names(child, separator)


class UserCreateWizard(models.TransientModel):
    _name = 'hs.base.user.create.wizard'
    _description = 'User Create Wizard'

    @api.model
    def _lang_get(self):
        return self.env['res.lang'].get_installed()

    @api.model
    def _tz_get(self):
        return [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]

    employee_ids = fields.Many2many('hs.base.employee', string='Employees')
    initial_password = fields.Char('New User Initial Password', required=True)
    group_ids = fields.Many2many('res.groups', String='Groups')
    tz = fields.Selection(_tz_get, string='Timezone', default=lambda self: self._context.get('tz'))
    lang = fields.Selection(_lang_get, string='Language', default=lambda self: self.env.lang)

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        group_user = self.env.ref('base.group_user', raise_if_not_found=False)
        if group_user:
            if active_ids:
                res = {'employee_ids': active_ids, 'group_ids': [group_user.id], 'tz': self._context.get('tz'),
                       'lang': self.env.lang}
        return res

    @api.multi
    def create_user(self):
        self.ensure_one()
        self = self.with_context(tracking_disable=True, no_reset_password=True)
        user_dataset = self.env['res.users']
        for employee_id in self.employee_ids:
            user = user_dataset.search([('login', '=', employee_id.employee_no)])
            if not employee_id.user_id:
                if user:
                    employee_id.user_id = user
                    for group_id in self.group_ids.mapped('id'):
                        employee_id.user_id.groups_id = [4, group_id]
                else:
                    employee_id.user_id = user_dataset.create({'name': employee_id.name,
                                                               'login': employee_id.employee_no,
                                                               'password': self.initial_password,
                                                               'email': employee_id.employee_no,
                                                               'groups_id': self.group_ids,
                                                               'tz': self.tz,
                                                               'lang': self.lang})
            else:
                for group_id in self.group_ids.mapped('id'):
                    employee_id.user_id.groups_id = [4, group_id]
