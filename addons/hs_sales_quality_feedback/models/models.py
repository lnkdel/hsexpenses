# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HSCustomerAttitude(models.Model):
    _name = "hs.sales.customer.attitude"
    _description = "Customer Attitude"
    _order = 'sequence, name'

    name = fields.Char(string="Name", required=True)
    note = fields.Text('Note')
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Attitude name already exists!'),
    ]


class HsQualityFeedback(models.Model):
    _name = 'hs.sales.quality.feedback'
    _inherit = ['mail.thread']
    _rec_name = 'name'
    _description = '客户质量信息反馈'

    name = fields.Char(string='编号', required=True, )

    # 客户信息
    customer_id = fields.Many2one(comodel_name="hs.sales.customer", string="客户名称", required=True,
                                  track_visibility='onchange')
    contact_name = fields.Char(string="联系人名称", required=True)
    contact_number = fields.Char(string="联系人电话", required=True, )
    customer_address = fields.Char(string="收货地址", required=True, )
    customer_service_manager_id = fields.Many2one('hs.base.employee', required=True,
                                                  string='客户服务经理',
                                                  track_visibility='onchange')
    # 问题产品信息
    product_category = fields.Selection(string="产品类别", selection=[
        ('cfb', '碳纤维'),
        ('resin', '树脂'),
        ('fabric', '织物'),
        ('prepreg', '预浸料'),
        ('part', '制件'),
    ], required=True, track_visibility='onchange')
    product_model_name = fields.Char(string="产品规格", required=True, track_visibility='onchange')
    product_photo = fields.Many2many('ir.attachment', 'hs_sales_quality_feedback_photo_rel',
                                     'feedback_id', 'photo_id', string='附件（相贴或标识）')
    number_of_problem_products = fields.Float(string="问题产品数量",  required=True, track_visibility='onchange')
    value_of_problem_products = fields.Float(string="问题产品价值",  required=True, track_visibility='onchange')
    quality_feedback_type = fields.Selection(string="质量反馈等级", selection=[
        ('less', '一般：<2万元'),
        ('medium', '重大：2-10万元'),
        ('danger', '危机：>10万元'),
    ], required=True, track_visibility='onchange')
    customer_losses = fields.Float(string="客户损失", required=True, track_visibility='onchange')
    customer_losses_description = fields.Text(string="客户损失价值组成说明")
    business_losses = fields.Float(string="业务损失", required=True, track_visibility='onchange')
    business_losses_description = fields.Text(string="业务损失价值组成说明")

    # 问题出现环节
    segment = fields.Selection(string="问题出现环节", selection=[
        ('retest', '入场复验'), ('customer', '客户下游客户'), ('other', '其他'), ], required=False, )
    use_process = fields.Selection(string="使用过程", selection=[
        ('unwinding', '退丝'), ('unfold fiber', '展纤'), ('other', '织造'),
        ('retest', '涂膜'), ('customer', '预浸'), ('other', '裁剪'),
        ('retest', '铺贴'), ('customer', '卷曲'), ('other', '固化'), ('other', '装配')], required=False, )
    other_description = fields.Text('其他描述')

    # 问题表征
    problem_representation = fields.Selection(string="问题表征", selection=[
        ('retest', '数量不足'), ('customer', '包装破损'), ('other', '外观（包括尺寸）不合格'),
        ('retest', '物理性能不合格'), ('customer', '力学性能不合格'), ('other', '操作问题'),
        ('retest', '试验不合格(静力、试飞等)'), ('customer', '不符合法规要求如：RoHS、REACH等'),
        ('other', '其他')], required=False, )
    problem_representation_description = fields.Text('其他表征描述')

    # 客户态度
    customer_attitude = fields.Many2many()
    customer_attitude_ids = fields.Many2many('hs.sales.customer.attitude',
                                             'hs_sales_customer_attitude_rel',
                                             'feedback_id', 'attitude_id',
                                             string='客户态度')
    expected_feedback_time = fields.Selection(string="客户期望反馈时间", selection=[
        ('short', '1-2天'), ('medium', '3-4天'), ('long', '5-6天'),], required=True, )
    return_list = fields.Many2many('ir.attachment', 'hs_sales_quality_feedback_return_list_rel',
                                   'feedback_id', 'return_list_id', string='退货清单')
    replenish_quantity = fields.Float(string='补货数量')
    compensation_amount = fields.Float(string='赔偿金额')

    remark = fields.Text('备注')

    @api.model
    def create(self, values):
        if values.get('name') is None or values.get('name') is False:
            name = self.env['ir.sequence'].next_by_code('hs.sales.quality.feedback.no')
            values['name'] = name

        return super(HsQualityFeedback, self).create(values)



