# -*- coding: utf-8 -*-
from myaddons.flowmanager.models import oa
from odoo import models, fields, api


class oa_flow(models.Model):
    _name = 'oa.flow'
    _rec_name = 'oaflow_name'

    ISPASS = [('1', '可跳过'), ('2', '不可跳')]

    oaflow_createperson = fields.Char(string='创建人', readonly=False,
                                      default=lambda self: self.env['res.users'].browse(self.env.uid).name)
    oaflow_name = fields.Char(string='流程名称')
    oaflow_flowtype = fields.Many2one('oa.ordertype', string='单子类型')

    oaflow_lines = fields.One2many('oa.flow.line', 'line_id', string='流程行')

    oaflow_passapprove = fields.Selection(ISPASS, string='同人员跳批', default='1')

    model_name = fields.Char(related='oaflow_flowtype.model_name.model', readonly=True, store=True)

    @api.model
    def create(self, vals):
        ordertype = self.env['oa.ordertype'].search([('id', '=', vals.get('oaflow_flowtype'))])
        vals.setdefault('oaflow_name', ordertype.name.replace("单", "") + "流程")
        oa_flowway = super(oa_flow, self).create(vals)
        return oa_flowway

    @api.multi
    def write(self, vals):
        if 'oaflow_flowtype' in vals:
            oaflow_flowtype = vals.get('oaflow_flowtype')
            ordertype = self.env['oa.ordertype'].search([('id', '=', oaflow_flowtype)])
            vals.setdefault('oaflow_name', str(ordertype.name).replace("单", "") + "流程")
        order = super(oa_flow, self).write(vals)
        return order


class oa_flow_line(models.Model):
    _name = 'oa.flow.line'

    line_id3 = fields.Many2one('res.partner', string='客户序号')
    line_id = fields.Many2one('oa.flow', string='每一行的ID')
    positer_id = fields.Many2one('hr.job', string='岗位', store=True)
    department_id = fields.Many2one('hr.department', string='部门', store=True)
    candidate_ids = fields.Many2many('hr.employee', string='候选人')
    approvalnumber = fields.Selection(oa.POSITION, string='审批步骤')
    positer_desc = fields.Char(string='审批步骤名称')
    isteamapproval = fields.Selection([('0', '是'), ('1', '否')], string='是否团队审批', copy=False, index=True, store=True, )
    model_name = fields.Char('模型名称')
    condivalue = fields.Char('条件')

    # node_from = fields.Many2one('oa.flow.line', string='前流程行')
    # node_to = fields.Many2one('oa.flow.line', string='后流程行')


class oa_flow_line_content(models.Model):
    _name = 'oa.flow.line.content'

    line_lvcid = fields.Many2one('oa', string='序号')
    positer_id = fields.Many2one('hr.job', string='岗位', store=True)
    department_id = fields.Many2one('hr.department', string='部门', store=True)
    candidate_ids = fields.Many2many('hr.employee', string='候选人')
    approvalnumber = fields.Selection(oa.POSITION, string='审批步骤')
    positer_desc = fields.Char(string='审批步骤名称')
    positer_state = fields.Selection([('1', '已提交'), ('2', '已通过'), ('3', '已驳回')], string='阶段审批状态', copy=False,
                                     index=True)
    isteamapproval = fields.Selection([('0', '是'), ('1', '否')], string='是否团队审批', copy=False, index=True, store=True, )


class oa_flow_step(models.Model):
    _name = 'oa.flow.step'

    step_lvid = fields.Many2one('oa', string='单号')
    step_name = fields.Char('步骤名称')
    operator = fields.Char(string='操作人')
    operatingresult = fields.Char(string='操作结果')
    operatingtime = fields.Char(string='操作时间')
    operatingdesc = fields.Char(string='处理意见')

    @api.model
    def default_get(self, fields_list):
        res = super(oa_flow_step, self).default_get(fields_list)
        oa_order = self.env['oa'].browse(self.env.context.get('active_id'))
        res.update({
            'step_lvid': oa_order.id
        })
        return res

    def action_reject(self):
        '''
        驳回操作
        :return:
        '''
        self.step_lvid.update({
            'oa_comment': self.operatingdesc
        })
        self.step_lvid.action_sure()

    def action_reject_all(self):
        '''
        驳回所有，回到审批人
        :return:
        '''
        self.step_lvid.update({
            'oa_comment': self.operatingdesc
        })
        self.step_lvid.action_goback_to_approve()
