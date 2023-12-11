# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime


PROVINCES = [
    ('bj', '北京市'),
    ('tj', '天津市'),
    ('sh', '上海市'),
    ('cq', '重庆市'),
    ('he', '河北省'),
    ('sx', '山西省'),
    ('ln', '辽宁省'),
    ('jl', '吉林省'),
    ('hlj', '黑龙江省'),
    ('js', '江苏省'),
    ('zj', '浙江省'),
    ('ah', '安徽省'),
    ('fj', '福建省'),
    ('jx', '江西省'),
    ('sd', '山东省'),
    ('hen', '河南省'),
    ('hb', '湖北省'),
    ('hn', '湖南省'),
    ('gd', '广东省'),
    ('hi', '海南省'),
    ('sc', '四川省'),
    ('gz', '贵州省'),
    ('yn', '云南省'),
    ('sn', '陕西省'),
    ('gs', '甘肃省'),
    ('qh', '青海省'),
    ('tw', '台湾省'),
    ('nm', '内蒙古自治区'),
    ('gx', '广西壮族自治区'),
    ('xz', '西藏自治区'),
    ('nx', '宁夏回族自治区'),
    ('xj', '新疆维吾尔自治区'),
    ('xg', '香港特别行政区'),
    ('am', '澳门特别行政区'),
    ('gw', '国外')
]
this_year = datetime.now().year
YEAR_SELECTION = [(this_year + i, str(this_year + i)) for i in range(-1, 4)]
MONTH_SELECTION = [(i, str(i)) for i in range(1, 13)]


class SalesForecast(models.Model):
    _name = 'hs.sales.forecast'
    _description = '销售预测'
    _order = 'create_date DESC'

    @api.model
    def _get_default_employee(self):
        return self.env['hs.base.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)

    product_category_id = fields.Many2one(comodel_name="hs.product.category", string="产品大类", required=True, )
    product_type_id = fields.Many2one(comodel_name="hs.product.type", string="产品小类", required=True,)
    product_specification_id = fields.Many2one(comodel_name="hs.product.specification", string="产品规格", required=False, )
    market_id = fields.Many2one(comodel_name="hs.sale.market", string="市场", required=True, )
    military_selection = fields.Selection(string="业务部门", selection=[('military', '军品'),
                                                                    ('not military', '非军品'), ], required=True, )
    manager_id = fields.Many2one('hs.base.employee', string='业务经理', required=True, default=_get_default_employee, )
    year_selection = fields.Selection(string="年份", selection=YEAR_SELECTION, default=this_year, required=True, )
    month_selection = fields.Selection(string="月份", selection=MONTH_SELECTION,
                                       default=datetime.now().month, required=True, )
    customer_id = fields.Many2one(comodel_name="hs.customer.profile", string="客户名称", required=True, )
    project_number = fields.Char(string="关联项目", required=False, )
    incremental_flag = fields.Selection(string="业务增/存量（是否新业务）", selection=[('incremental', '增量'), ('stock', '存量'), ],
                                        required=True, )
    customer_factory = fields.Char(string="客户工厂(终端)", required=True)
    customer_sale_area = fields.Selection(string="客户销售区域(省份/国别)", selection=PROVINCES, required=True)
    evaluate_price = fields.Float(string="合同基准价预测",  required=True, )
    month_requirement = fields.Float(string="客户总需求量", required=True, )
    expected_salable_wallet_share = fields.Float(string="预计可销售钱包份额，%",
                                                 compute='_compute_expected_salable_wallet_share')
    estimated_sales_volume = fields.Float(string="当月预计销售量", required=True, )
    next_month_w1 = fields.Float(string="第1周", required=False, )
    next_month_w2 = fields.Float(string="第2周", required=False, )
    next_month_w3 = fields.Float(string="第3周", required=False, )
    next_month_w4 = fields.Float(string="第4周", required=False, )
    unit = fields.Selection(string="单位", selection=[('kg', 'kg'), ('sq.m', 'sq.m'), ('件', '件'), ('m', 'm'), ],
                            required=True, )
    current_month_price = fields.Float(string="当月销售价格", required=True, )
    current_month_total_sales = fields.Float(string="月销售总额", compute='_compute_current_month_total_sales')
    currency = fields.Selection(string="币种", selection=[('rmb', '人民币'), ('other', '外币'), ], required=True, )
    customer_category = fields.Selection(string="客户属性", selection=[('end customer', '终端客户'),
                                                                   ('trader','贸易商'),
                                                                   ('agent','代理商')], required=True)
    place_of_delivery = fields.Char(string="发货工厂", required=True)
    payment_method = fields.Selection(string="付款方式", selection=[('cash', '现结'), ('credit', '赊销'), ], required=True, )
    payment_days = fields.Integer(string="付款天数", required=True, )
    cooperate = fields.Selection(string="是否合作（是否新客户）", selection=[('yes', '是'), ('no', '否'), ], required=True, )
    remark = fields.Text(string="备注", required=False, )

    @api.one
    @api.depends('current_month_price','estimated_sales_volume')
    def _compute_current_month_total_sales(self):
        for rec in self:
            rec.current_month_total_sales = rec.current_month_price * rec.estimated_sales_volume

    @api.one
    @api.depends('estimated_sales_volume', 'month_requirement')
    def _compute_expected_salable_wallet_share(self):
        if self.month_requirement != 0:
            self.expected_salable_wallet_share = (self.estimated_sales_volume / self.month_requirement) * 100

    @api.onchange('product_category_id')
    def _onchange_product_category_id(self):
        self.product_type_id = False
        self.product_specification_id = False
        if self.product_category_id:
            return {'domain': {'product_type_id': [('category_id', '=', self.product_category_id.id)],
                               'product_specification_id': [('category_id', '=', self.product_category_id.id)]}}
        else:
            return {'domain': {'product_type_id': [], 'product_specification_id': []}}

    # @api.onchange('product_type_id')
    # def _onchange_product_type_id(self):
    #     self.product_specification_id = False
    #     if self.product_type_id:
    #         return {'domain': {'product_specification_id': [('type_id', '=', self.product_type_id.id)]}}
    #     else:
    #         return {'domain': {'product_specification_id': []}}


class ProductCategory(models.Model):
    _name = 'hs.product.category'
    _rec_name = 'name'
    _description = '产品大类'

    name = fields.Char(string="名称", required=True,)
    sequence = fields.Integer(string="排序", default=10)
    active = fields.Boolean(string='是否显示？', default=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)', "名称已经存在！")
    ]


class ProductType(models.Model):
    _name = 'hs.product.type'
    _rec_name = 'name'
    _description = '产品小类'

    name = fields.Char(string="名称", required=True,)
    category_id = fields.Many2one(comodel_name="hs.product.category", string="产品大类", required=True, )
    sequence = fields.Integer(string="排序", default=10)
    active = fields.Boolean(string='是否显示？', default=True)

    _sql_constraints = [
        ('name_unique', 'unique(name)', "名称已经存在！")
    ]


class ProductSpecification(models.Model):
    _name = 'hs.product.specification'
    _rec_name = 'name'
    _description = '产品规格'

    name = fields.Char(string="名称", required=True,)
    # type_id = fields.Many2one(comodel_name="hs.product.type", string="产品小类", required=True, )
    category_id = fields.Many2one(comodel_name="hs.product.category", string="产品大类", required=True, )
    sequence = fields.Integer(string="排序", default=10)
    active = fields.Boolean(string='是否显示？', default=True)

    _sql_constraints = [
        ('name_unique', 'unique(name, category_id)', "该类别下名称已经存在！")
    ]






