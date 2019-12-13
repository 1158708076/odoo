from odoo import models, fields, api
from odoo.osv import osv


class oa_purchase_order(models.Model):
    _inherit = 'purchase.order'

    resourceflow = fields.Many2one('oa', string='源流程')
    oa_state = fields.Selection(string='流程状态', related='resourceflow.oa_state', store=True)

    @api.multi
    def action_submit(self):
        ordertype = self.env['oa.ordertype'].search([('code', '=', '3')])
        typename = ordertype.name
        newformname = self.env['ir.sequence'].search([('name', '=', typename)]).next_by_id()
        order = self.env['oa'].create({
            'oa_application': self.env['hr.employee'].search([('name', '=', self.env.user.name)]).id,
            'x_purchase_order': self.id,
            'oa_name': newformname,
            'oa_state': 'nosubmit',
            'oa_ordertype': '3',
        })
        order.get_oa_flowway(3)
        order.get_candidate()
        a = int(0.0)
        for line in order.oa_flowwaylines:
            a += 1
            if a == 1:
                order.oa_approver = line.candidate_ids
            elif a == 2:
                order.oa_nextapprover = line.candidate_ids
        order.action_commit()
        # self.state = 'done'

    @api.multi
    def action_approve(self):
        uname = self.env['res.users'].browse(self.env.uid).name
        uinfo = self.env['hr.employee'].search([('name', '=', uname)])
        oaorder = self.env['oa'].search([('x_purchase_order', '=', self.id)])
        if uinfo.id in oaorder.oa_approver._ids:
            mainactivitys = self.env['mail.activity'].search(
                [('res_name', '=', oaorder.oa_name)])
            mainactivitys2 = self.env['mail.activity'].search(
                [('res_name', '=', self.name)])
            for mainactivity in mainactivitys:
                mainactivity.action_done()
            for mainactivity in mainactivitys2:
                mainactivity.action_done()
            oaorder.action_approve_pass()
        else:
            raise osv.except_osv('当前审批人不是你！')

    @api.multi
    def write(self, vals):
        if 'order_line' in vals and self.oa_state != 'nosubmit' and self.oa_state != False:
            raise osv.except_osv('订单审批中，不可修改！')
        else:
            return super(oa_purchase_order, self).write(vals)
