from myaddons.utils import util
from odoo import models, fields, api


class oa_entrust(models.Model):
    _name = 'oa.entrust'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = '流程委托'
    _rec_name = 'et_name'

    def _default_et_from(self):
        user_name = self.env['res.users'].browse(self.env.uid).name
        employee = self.env['hr.employee'].search([('name', '=', user_name)], limit=1)
        return employee

    et_name = fields.Char(string='委托名称', readonly=True)
    et_from = fields.Many2one('hr.employee', string='委托人', default=_default_et_from)
    et_to = fields.Many2one('hr.employee', string='被委托人')
    et_start = fields.Datetime(string='委托开始')
    et_end = fields.Datetime(string='委托结束')
    et_how = fields.Selection(selection=[('1', '全部'), ('2', '部分')], string='选择')
    et_type = fields.Many2many('oa.ordertype', 'entrust_ordertype_rel', 'entrust_id', 'type_id', string='委托类型')

    @api.onchange('et_how')
    def _onchange_et_how(self):
        if self.et_how == '1':
            ordertypes = self.env['oa.ordertype'].search([])
            self.et_type = [[6, 0, ordertypes.ids]]

    @api.model
    def create(self, vals):
        etfrom = vals.get('et_from')
        etto = vals.get('et_to')
        etfromname = self.env['hr.employee'].browse(etfrom).name
        ettoname = self.env['hr.employee'].browse(etto).name
        etname = '委托（%s → %s）' % (etfromname, ettoname)
        vals.setdefault('et_name', etname)
        order = super(oa_entrust, self).create(vals)
        util.mail_activity.send_message(order, self._name, order.et_to.user_id.id, '委托')
        return order

    @api.multi
    def write(self, vals):
        etfromname = self.et_from.name
        ettoname = self.et_to.name

        if vals.get('et_from'):
            etfrom = vals.get('et_from')
            etfromname = self.env['hr.employee'].browse(etfrom).name
        if vals.get('et_to'):
            etto = vals.get('et_to')
            ettoname = self.env['hr.employee'].browse(etto).name
        etname = '委托（%s → %s）' % (etfromname, ettoname)
        vals.setdefault('et_name', etname)
        if 'et_to' in vals:
            etto = self.env['hr.employee'].browse(vals.get('et_to'))
            util.mail_activity.send_message(self, self._name, etto.user_id.id, '委托')
        order = super(oa_entrust, self).write(vals)
        return order
