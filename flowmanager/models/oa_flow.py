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

    is_workflow = fields.Boolean(string='是否加入工作流', default=False, help='默认为审批流，如果加入工作流，流程定义会改为审批工作流程的流程定义')

    @api.model
    def create(self, vals):
        if 'oaflow_flowtype' in vals:
            ordertype = self.env['oa.ordertype'].search([('id', '=', vals.get('oaflow_flowtype'))])
            vals.setdefault('oaflow_name', ordertype.name.replace("单", "") + "流程")
        oa_flowway = super(oa_flow, self).create(vals)
        if vals.get('is_workflow'):
            oa_flowway.creat_server_actions()
        return oa_flowway

    @api.multi
    def write(self, vals):
        if 'oaflow_flowtype' in vals:
            oaflow_flowtype = vals.get('oaflow_flowtype')
            ordertype = self.env['oa.ordertype'].search([('id', '=', oaflow_flowtype)])
            vals.setdefault('oaflow_name', str(ordertype.name).replace("单", "") + "流程")
        order = super(oa_flow, self).write(vals)
        if self.is_workflow or vals.get('is_workflow'):
            self.update_server_actions()
        return order

    def creat_server_actions(self):
        for line in self.oaflow_lines:
            server = self.env['ir.actions.server'].create({
                'name': line.positer_desc,
                'model_id': line.wf_model_id.id,
                # 控制服务器动作按钮出现在哪个模型
                'binding_model_id': line.wf_model_id.id,
                'state': 'code',
                'code': line.wf_code,
            })
            line.update({
                'server_id': server.id
            })

    def update_server_actions(self):
        for line in self.oaflow_lines:
            serverid = self.env['ir.actions.server'].search([('id', '=', line.server_id)])
            if serverid:
                serverid.update({
                    'name': line.positer_desc,
                    'model_id': line.wf_model_id.id,
                    'binding_model_id': line.wf_model_id.id,
                    'code': line.wf_code,
                })
            else:
                server = self.env['ir.actions.server'].create({
                    'name': line.positer_desc,
                    'model_id': line.wf_model_id.id,
                    'binding_model_id': line.wf_model_id.id,
                    'state': 'code',
                    'code': line.wf_code,
                })
                line.update({
                    'server_id': server.id
                })


class oa_flow_line(models.Model):
    _name = 'oa.flow.line'

    line_id3 = fields.Many2one('res.partner', string='客户序号')
    line_id = fields.Many2one('oa.flow', string='每一行的ID')
    positer_id = fields.Many2one('hr.job', string='岗位', store=True)
    department_id = fields.Many2one('hr.department', string='部门', store=True)
    candidate_ids = fields.Many2many('hr.employee', string='候选人')
    approvalnumber = fields.Selection(oa.POSITION, string='审批步骤', help="选择步骤时，请不要重复")
    positer_desc = fields.Char(string='步骤名称')
    isteamapproval = fields.Selection([('0', '是'), ('1', '否')], string='是否团队审批', copy=False, index=True, store=True, )
    model_name = fields.Char('模型名称')
    condivalue = fields.Char('条件')

    wf_model_id = fields.Many2one('ir.model', string='模型')
    wf_code = fields.Text(string='执行代码',
                          help='''帮助使用Python表达式
变量字段也许要用到Python 代码或Python 的表达式。以下的变量能够使用
env：触发​​操作的Odoo环境
model：在其上触发操作的记录的Odoo模型；是无效的记录集
record：记录触发操作的记录；可能是空的
records：以多模式触发操作的所有记录的记录集；可能是无效的
time，datetime，dateutil，timezone：有用的Python库
log(message, level='info')：logging函数将调试信息记录在ir.logging表中
Warning：警告与异常一起使用 raise
要返回动作，请分配： action = {...}

Python代码示例
partner_name = record.name + '_code'
env['res.partner'].create({'name': partner_name})
                          ''')
    server_id = fields.Integer(string='服务器动作')

    # node_from = fields.Many2one('oa.flow.line', string='前流程行')
    # node_to = fields.Many2one('oa.flow.line', string='后流程行')

    def unlink(self):
        server = self.env['ir.actions.server'].search([('id', '=', self.server_id)])
        server.unlink()
        return super(oa_flow_line, self).unlink()


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

    @api.model
    def _getRejectperosn(self):
        persons = []
        oa = self.env['oa'].search([('id', '=', self._context.get('default_step_lvid'))])
        cn1 = (-2, "上一级")
        cn2 = (-1, "申请人")
        persons.append(cn1)
        persons.append(cn2)
        for line in oa.oa_flowwaylines:
            line_number = line.approvalnumber
            can_name = []
            for can in line.candidate_ids:
                can_name.append(can.name)
            cn = (line_number, can_name)
            persons.append(cn)
        return persons

    step_lvid = fields.Many2one('oa', string='单号')
    step_name = fields.Char('步骤名称')
    operator = fields.Char(string='操作人')
    operatingresult = fields.Char(string='操作结果')
    operatingtime = fields.Char(string='操作时间')
    operatingdesc = fields.Char(string='处理意见')
    rejectToperson = fields.Selection(selection=_getRejectperosn, string="驳回到", default=-2)

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

        oa = self.env['oa'].search([('id', '=', self._context.get('default_step_lvid'))])
        oa.write({
            'oa_comment': self.operatingdesc
        })
        if self.rejectToperson == '-2':
            # 驳回到上一级
            oa.action_sure()
        elif self.rejectToperson == '-1':
            # 驳回到申请人
            oa.action_goback_to_approve()
        else:
            # 驳回到某个人
            oa.action_approve_rejected_toSomeOne(self.rejectToperson)
