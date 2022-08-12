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
    _rec_name = 'name'
    _description = '事项'

    name = fields.Char(string="标题")
    start_date = fields.Date(string='开始时间', required=True, default=lambda self: fields.Date.context_today(self))
    end_date = fields.Date(string='结束时间', required=True, default=lambda self: fields.Date.context_today(self))
    event_category_id = fields.Many2one(comodel_name="hs.event.category", string="事项类型", required=True, )
    charge_id = fields.Many2one('hs.base.employee', string="负责人", required=True)
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
        ('cancel', '取消'), ], default='draft')
    remark = fields.Text(string="备注", required=False, )
    content = fields.Html(string="内容", )
    annotation_ids = fields.One2many(comodel_name="hs.event.annotation", inverse_name="event_id", string="批注",
                                     required=False, )
    score = fields.Integer(string="分数", required=False, readonly=True )
    department_id = fields.Many2one('hs.base.department', string="部门", related='charge_id.department_id', store=True)
    sequence = fields.Integer(string="排序", default=0)

    @api.multi
    def write(self, values):
        if 'state' in values:
            if self.state == "delay":
                values['state'] = "delay"
        return super(Event, self).write(values)

    @api.constrains('score')
    def _check_score(self):
        for record in self:
            if record.score > 10 or record.score < 0:
                raise UserError("分数必须在0～10之间！")

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
        pass

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


class EventAnnotation(models.Model):
    _name = 'hs.event.annotation'
    _description = '批注'

    event_id = fields.Many2one(comodel_name="hs.event", string="事项", )
    content = fields.Text(string="内容", required=False, )
    annotation_date = fields.Datetime(string='批注时间', default=fields.Datetime.now)
    attachment_ids = fields.Many2many('ir.attachment',
                                      'hs_event_annotation_attachment_rel',
                                      'annotation_id',
                                      'attachment_id',
                                      string='附件')
    employee_id = fields.Many2one('hs.base.employee', string='批注者', required=True)


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



