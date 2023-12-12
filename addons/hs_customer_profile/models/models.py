# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

UNIT_SELECT_ITEM = [('kg', '公斤'), ('sq.m', '平方米'), ('m', '米'), ('e.a.', '件'), ]

PRODUCT_TYPE = [('carbon fibre', '碳纤维'),
                ('prepreg', '预浸料'),
                ('fabric', '织物'),
                ('part', '制品制件'),
                ('carbon plate', '拉挤碳板'),
                ('technical service', '技术服务'), ]

this_year = datetime.now().year

YEAR_SELECT_ITEM = [(this_year + i, str(this_year + i)) for i in range(-5, 4)]


class CustomerIndustry(models.Model):
    _name = 'hs.customer.industry'
    _rec_name = 'name'
    _description = '行业'
    _order = 'sequence'

    name = fields.Char(string="名称")
    sequence = fields.Integer(string="排序", default=10)
    active = fields.Boolean(string='有效?', default=True)


class CustomerEmployee(models.Model):
    _name = 'hs.customer.employee'
    _rec_name = 'name'
    _description = '客户人员'

    name = fields.Char(string="姓名")
    position = fields.Char(string="职位", required=False, )
    mobile = fields.Char(string="联系方式", required=False, )
    customer_id = fields.Many2one(comodel_name="hs.customer.profile", string="客户公司", required=False, )


class ConditionBusiness(models.Model):
    _name = 'hs.customer.condition.business'
    _description = '客户经营情况'

    device_type = fields.Char(string="设备类型")
    device_count = fields.Char(string="设备数量")
    product_type = fields.Selection(string="需求产品大类", selection=PRODUCT_TYPE, required=False, )
    requirement_one_year_product = fields.Char(string="需求产品规格")
    requirement_one_year = fields.Float(string="年需求量")
    requirement_one_year_unit = fields.Selection(string="单位", selection=UNIT_SELECT_ITEM, required=False, )
    customer_customer_name = fields.Char(string="终端客户", required=False, )
    customer_id = fields.Many2one(comodel_name="hs.customer.profile", string="客户公司", required=False, )

    @api.onchange('product_type')
    def _onchange_product_type(self):
        if self.product_type == 'carbon fibre' or self.product_type == 'fabric':
            self.requirement_one_year_unit = 'kg'
        elif self.product_type == 'prepreg' or self.product_type == 'carbon plate':
            self.requirement_one_year_unit = 'sq.m'
        elif self.product_type == 'part':
            self.requirement_one_year_unit = 'e.a.'
        else:
            self.requirement_one_year_unit = ''


class CustomerTransactionRecord(models.Model):
    _name = 'hs.customer.transaction.record'
    _description = '成交记录'

    # transaction_time = fields.Datetime(string="成交时间", required=False, )
    # transaction_year = fields.Date(string="成交时间", required=False, )
    transaction_year = fields.Selection(string="成交时间(年)", selection=YEAR_SELECT_ITEM, default=this_year,
                                        required=False, )
    product_name = fields.Char(string="购买重点产品规格", required=False, )
    product_type = fields.Selection(string="产品大类", selection=PRODUCT_TYPE, required=False, )
    price = fields.Float(string="成交单价", required=False, )
    amount_of_transaction = fields.Float(string="成交数量", required=False, )
    unit = fields.Selection(string="单位", selection=UNIT_SELECT_ITEM, required=False, )
    amount = fields.Float(string="成交金额", required=False, )
    customer_id = fields.Many2one(comodel_name="hs.customer.profile", string="客户公司", required=False, )
    remark = fields.Text(string="备注", required=False, )

    @api.onchange('amount_of_transaction', 'price')
    def _onchange_price(self):
        self.amount = self.amount_of_transaction * self.price

    @api.onchange('product_type')
    def _onchange_product_type(self):
        if self.product_type == 'carbon fibre' or self.product_type == 'fabric':
            self.unit = 'kg'
        elif self.product_type == 'prepreg' or self.product_type == 'carbon plate':
            self.unit = 'sq.m'
        elif self.product_type == 'part':
            self.unit = 'e.a.'
        else:
            self.unit = ''


class CustomerProfile(models.Model):
    _name = 'hs.customer.profile'
    _rec_name = 'name'
    _description = '客户档案'

    name = fields.Char(string="名称", required=True)
    customer_no_id = fields.Many2one('hs.base.customer.number', required=True, string='客户编码')
    customer_level = fields.Selection(string="客户等级", selection=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ],
                                      required=True, )
    employee_id = fields.Many2one('hs.base.employee', string='业务员', required=True,
                                  default=lambda self: self.env['hs.base.employee'].sudo().search(
                                      [('user_id', '=', self.env.uid)], limit=1))
    customer_address = fields.Char(string="客户地址", required=False, )
    postal_code = fields.Char(string="邮政编码", required=False, )
    customer_site_address = fields.Char(string="客户企业网址", required=False, )
    customer_tel = fields.Char(string="公司电话", required=False, )
    legal_person_name = fields.Char(string="法人", required=False, )
    registered_capital_money = fields.Float(string="注册资本", required=False, )
    registered_capital_unit = fields.Selection(string="注册资本单位", selection=[('yuan', '元'), ('wanyuan', '万元'),
                                                                           ('yiyuan', '亿元'), ],
                                               default='wanyuan', required=False, )
    registered_capital_currency = fields.Selection(string="注册资本币种", selection=[('rmb', '人民币'), ('usd', '美元'), ],
                                                   default='rmb', required=False, )
    begin_date = fields.Date(string="成立日期", required=False, default=lambda self: fields.Date(self).today())
    organization_type = fields.Selection(string="组织形态", selection=[('state-owned', '国企'), ('foreign', '外企'),
                                                                   ('private', '私企'), ('government', '政府机构'),
                                                                   ('university', '院校'), ('other', '其他'), ],
                                         required=False, )
    employee_count = fields.Integer(string="人员规模", required=False, )
    industry_id = fields.Many2one(comodel_name="hs.customer.industry", string="所属行业", required=False, )
    sale_area_id = fields.Many2one('hs.sale.area', string='所在区域', )
    # device_type = fields.Char(string="设备类型")
    # device_count = fields.Char(string="设备数量")
    # requirement_one_year = fields.Float(string="年需求量")
    # customer_customer_name = fields.Char(string="终端客户", required=False, )
    # requirement_one_year_unit = fields.Char(string="年需求量单位")
    # requirement_one_year_product = fields.Char(string="需求产品")
    management_description = fields.Text(string="主要经营范围", required=False, )
    affiliated_companies = fields.Text(string="关联公司情况", required=False, )
    customer_employee_ids = fields.One2many(comodel_name="hs.customer.employee", inverse_name="customer_id",
                                            string="主要人员", required=False, )

    transaction_record_ids = fields.One2many(comodel_name="hs.customer.transaction.record", inverse_name="customer_id",
                                             string="成交记录", required=False, )
    condition_business_ids = fields.One2many(comodel_name="hs.customer.condition.business", inverse_name="customer_id",
                                             string="经营情况", required=False, )
    current_remark = fields.Text(string="公司目前政策", required=False, )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', '客户名称已存在!'),
        ('customer_no_id_uniq', 'unique(customer_no_id)', '客户编码已存在!'),
    ]

    @api.onchange('customer_no_id')
    def _onchange_customer_no_id(self):
        self.name = False
        if self.customer_no_id:
            customer_no_name = self.customer_no_id.name
            index = customer_no_name.rfind(".")
            if index != -1:
                self.name = customer_no_name[index+4:]
            else:
                self.name = customer_no_name
