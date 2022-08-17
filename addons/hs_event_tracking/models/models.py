# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime


class EventCategory(models.Model):
    _name = 'hs.event.category'
    _rec_name = 'name'
    _description = '事项类型'

    name = fields.Char(string="名称")
    sequence = fields.Integer(string="排序", default=0)
    active = fields.Boolean(string='是否显示?', default=True)


class Event(models.Model):
    _name = 'hs.event'
    _inherit = ['mail.thread']
    _rec_name = 'name'
    _description = '事项'

    name = fields.Char(string="标题", required=True, track_visibility='onchange')
    start_date = fields.Date(string='开始时间', required=True, default=lambda self: fields.Date.context_today(self)
                             , track_visibility='onchange')
    end_date = fields.Date(string='结束时间', required=True, default=lambda self: fields.Date.context_today(self)
                           , track_visibility='onchange')
    event_category_id = fields.Many2one(comodel_name="hs.event.category", string="事项类型", required=True
                                        , track_visibility='onchange')
    charge_id = fields.Many2one('hs.base.employee', string="负责人", required=True, track_visibility='onchange')
    player_ids = fields.Many2many(comodel_name="hs.base.employee", relation="hs_event_employee_rel",
                                  column1="event_id", column2="employee_id", string="参与人", )
    attachment_ids = fields.Many2many('ir.attachment',
                                      'hs_event_attachment_rel',
                                      'event_id',
                                      'attachment_id',
                                      string='附件')
    attachment_remark = fields.Text(string="附件说明", required=False, )

    state = fields.Selection(string="状态", selection=[
        ('draft', '草稿'),
        ('doing', '进行中'),
        ('done', '完成'),
        ('delay', '超期'),
        ('cancel', '取消'), ], default='draft', track_visibility='onchange')
    remark = fields.Text(string="备注", required=False, )
    content = fields.Html(string="内容", )
    annotation_ids = fields.One2many(comodel_name="hs.event.annotation", inverse_name="event_id", string="批注",
                                     required=False, )
    note_ids = fields.One2many(comodel_name="hs.event.note", inverse_name="event_id", string="进度日志",
                                     required=False, )
    score = fields.Integer(string="分数", required=False, readonly=True, track_visibility='onchange')
    department_id = fields.Many2one('hs.base.department', string="部门", related='charge_id.department_id', store=True)
    sequence = fields.Integer(string="排序", default=0)
    active = fields.Boolean(string='是否显示?', default=True, track_visibility='onchange')

    @api.multi
    def write(self, values):
        if 'state' in values:
            if not self.user_has_groups('hs_event_tracking.group_hs_event_tracking_manager'):
                values.pop('state')
                if 'event_category_id' in values:
                    values.pop('event_category_id')
                if 'name' in values:
                    values.pop('name')
                if 'start_date' in values:
                    values.pop('start_date')
                if 'end_date' in values:
                    values.pop('end_date')
                if 'charge_id' in values:
                    values.pop('charge_id')
                if 'player_ids' in values:
                    values.pop('player_ids')
                if 'attachment_ids' in values:
                    values.pop('attachment_ids')
                if 'content' in values:
                    values.pop('content')
            else:
                if self.state == "delay" and values['state'] != 'done':
                    values['state'] = "delay"
        return super(Event, self).write(values)

    @api.constrains('score')
    def _check_score(self):
        for record in self:
            if record.score > 10 or record.score < 0:
                raise ValidationError("分数必须在0～10之间！")

    @api.model
    def update_event_status(self):
        records = self.env['hs.event'].search([('state', '=', 'doing')])
        for record in records:
            now = datetime.datetime.now()
            end_time = datetime.datetime.combine(record.end_date, datetime.time.max)
            if now > end_time:
                record.state = "delay"

    @api.multi
    def action_submit_annotation(self):
        employee = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hs.event.annotation.wizard',
            'name': '批注向导',
            'view_mode': 'form',
            'context': {
                'event_id': self.id,
                'employee_id': employee.id
            },
            'target': 'new'
        }

    @api.multi
    def action_submit_score(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hs.event.score.wizard',
            'name': '打分向导',
            'view_mode': 'form',
            'context': {
                'event_id': self.id,
            },
            'target': 'new'
        }

    @api.multi
    def action_submit_note(self):
        employee = self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hs.event.note.wizard',
            'name': '撰写日志向导',
            'view_mode': 'form',
            'context': {
                'event_id': self.id,
                'employee_id': employee.id
            },
            'target': 'new'
        }


class EventAnnotation(models.Model):
    _name = 'hs.event.annotation'
    _description = '批注'

    event_id = fields.Many2one(comodel_name="hs.event", string="事项", required=True, )
    content = fields.Text(string="内容", required=True, )
    annotation_date = fields.Datetime(string='批注时间', default=fields.Datetime.now)
    attachment_ids = fields.Many2many('ir.attachment',
                                      'hs_event_annotation_attachment_rel',
                                      'annotation_id',
                                      'attachment_id',
                                      string='附件')
    employee_id = fields.Many2one('hs.base.employee', string='批注者', required=True)


class EventNote(models.Model):
    _name = 'hs.event.note'
    _rec_name = 'name'
    _description = '进度日志'

    @api.model
    def _get_default_employee(self):
        return self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    event_id = fields.Many2one(comodel_name="hs.event", string="事项", required=True, )
    name = fields.Char(string='标题', required=True)
    date_note = fields.Datetime(string='日志时间', required=True, default=fields.Datetime.now)
    employee_id = fields.Many2one('hs.base.employee', string='员工', required=True,
                                  default=_get_default_employee,
                                  ondelete='restrict')
    description = fields.Html('进度详情')
    percent_complete = fields.Float(string="完成百分比",  required=True, )
    percent_last = fields.Float(string="上次进度值", compute='_compute_percent_last')
    attachment_ids = fields.Many2many('ir.attachment',
                                      'hs_event_note_attachment_rel',
                                      'note_id',
                                      'attachment_id',
                                      string='附件')

    @api.one
    @api.depends('employee_id', 'event_id')
    def _compute_percent_last(self):
        notes = self.env['hs.event.note'].search([('event_id', '=', self.event_id.id), ('employee_id', '=', self.employee_id.id)], order='percent_complete desc')
        if notes is not None and len(notes) > 0:
            self.percent_last = notes[0].percent_complete


class EventCancelWizard(models.TransientModel):
    _name = 'hs.event.cancel.wizard'
    _description = '事项取消向导'

    event_ids = fields.Many2many('hs.event', string='事项')

    @api.model
    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        if active_ids:
            events = self.env['hs.event'].search_read(
                domain=[('id', 'in', active_ids)], fields=['id', 'state'])
            ids = [s['id'] for s in list(filter(lambda s: s['state'] == 'doing', events))]
            res = {'event_ids': ids}
        return res

    def save_button(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids')
        if active_ids:
            events = self.env['hs.event'].search([
                ('id', 'in', active_ids),
                ('state', '=', 'doing')])
            events.write({'state': 'cancel'})
        return {'type': 'ir.actions.act_window_close'}


class EventScoreWizard(models.TransientModel):
    _name = 'hs.event.score.wizard'
    _description = '打分向导'

    score = fields.Selection(string="分数",
                             selection=[('10', '10'), ('9', '9'), ('8', '8'), ('7', '7'), ('6', '6'),
                                        ('5', '5'), ('4', '4'), ('3', '3'), ('2', '2'), ('1', '1'), ('0', '0'), ],
                             required=True, copy=False, default="8")

    def save_button(self):
        event_id = self.env.context.get('event_id')
        event = self.env['hs.event'].browse(int(event_id))
        score_num = int(self.score)
        event.write({'score': score_num})
        return True


class EventAnnotationWizard(models.TransientModel):
    _name = 'hs.event.annotation.wizard'
    _description = '批注向导'

    content = fields.Text(string="内容", required=True, )
    attachment_ids = fields.Many2many('ir.attachment',
                                      'hs_event_annotation_wizard_attachment_rel',
                                      'annotation_wizard_id',
                                      'attachment_id',
                                      string='附件')

    def save_button(self):
        event_id = self.env.context.get('event_id')
        # event = self.env['hs.event'].browse(int(event_id))
        employee_id = self.env.context.get('employee_id')
        att_ids = [attachment_id.id for attachment_id in self.attachment_ids]
        annotation = self.env['hs.event.annotation'].create({'event_id': event_id,
                                                             'content': self.content,
                                                             'attachment_ids': [(6, 0, att_ids)],
                                                             'annotation_date': datetime.datetime.now(),
                                                             'employee_id': employee_id
                                                             })
        return True


class EventNoteWizard(models.TransientModel):
    _name = 'hs.event.note.wizard'
    _description = '撰写日志向导'

    note_ids = fields.Many2many('hs.event.note', string='日志')
    name = fields.Char(string='标题', required=True)
    description = fields.Html('进度详情')
    attachment_ids = fields.Many2many('ir.attachment',
                                      'hs_event_note_wizard_attachment_rel',
                                      'note_wizard_id',
                                      'attachment_id',
                                      string='附件')
    percent_complete = fields.Float(string="完成百分比", required=True, )
    percent_last = fields.Float(string="上次进度值")

    @api.model
    def default_get(self, fields):
        res = {}
        event_id = self.env.context.get('event_id')
        employee_id = self.env.context.get('employee_id')
        if event_id:
            notes = self.env['hs.event.note'].search_read(domain=[
                ('event_id', '=', event_id),
                ('employee_id', '=', employee_id)], fields=['id', 'percent_complete'], order='percent_complete desc')
            ids = [s['id'] for s in notes]
            last_percent = 0
            if notes is not None and len(notes) > 0:
                last_percent = notes[0]['percent_complete']
            res = {'note_ids': ids, 'percent_last': last_percent}
        return res

    def save_button(self):
        event_id = self.env.context.get('event_id')
        # event = self.env['hs.event'].browse(int(event_id))
        employee_id = self.env.context.get('employee_id')
        att_ids = [attachment_id.id for attachment_id in self.attachment_ids]
        if self.percent_complete == 0 or self.percent_complete < self.percent_last:
            raise UserError("请输入合适的完成百分比！")
        note = self.env['hs.event.note'].create({'event_id': event_id,
                                                 'name': self.name,
                                                 'date_note': datetime.datetime.now(),
                                                 'employee_id': employee_id,
                                                 'description': self.description,
                                                 'percent_complete': self.percent_complete,
                                                 'attachment_ids': [(6, 0, att_ids)]})
        return True
