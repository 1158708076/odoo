# -*- coding: utf-8 -*-
import datetime
import logging

import requests

from odoo import models, fields, api
from odoo.osv import osv

POSITION = [('p0', 'p0'), ('p1', 'p1'), ('p2', 'p2'), ('p3', 'p3'), ('p4', 'p4'), ('p5', 'p5'), ('p6', 'p6'),
            ('p7', 'p7'), ('p8', 'p8'), ('p9', 'p9'), ('p10', 'p10')]

_logger = logging.getLogger(__name__)


class oa(models.Model):
    _name = 'oa'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'oa_name'
    _order = 'oa_createdate desc'
    _description = '流程单'

    def _default_oa_applicant(self):
        uname = self.env['res.users'].browse(self.env.uid).name
        uinfo = self.env['hr.employee'].search([('name', '=', uname)])
        return self.env['hr.employee'].search([('name', '=', uinfo.name)], limit=1)

    ismark = [('1', '被标记'), ('0', '未被标记')]
    oa_name = fields.Char(string='名称', index=True, )
    oa_createdate = fields.Date(string='创建时间', readonly=False, default=fields.Date.context_today)
    oa_applicant = fields.Many2one('hr.employee', string='申请人', readonly=True, default=_default_oa_applicant)
    user_id = fields.Many2one('res.users', string='申请人id', default=lambda self: self.env.user,
                              index=True, required=True)
    oa_approver = fields.Many2many('hr.employee', 'oa_oa_approver_hr_employee_rel', string='当前审批人', required=True)
    oa_nextapprover = fields.Many2many('hr.employee', 'oa_oa_nextapprover_hr_employee_rel', string='下一级审批人',
                                       required=True)
    oa_state = fields.Selection([
        ('nosubmit', '草稿'),
        ('noapprove', '待审批'),
        ('approving', '审批中'),
        ('ok', '完成'), ('goback', '被驳回'), ('editing', '编辑中'), ('termination', '终止')], string='状态',
        copy=False,
        index=True,
        readonly=True, store=True)
    oa_flowway = fields.Many2one('oa.flow', string="流程名称", readonly=False)
    oa_flowwaylines = fields.One2many('oa.flow.line.content', 'line_lvcid', string='流程行')
    oa_flowwaysteps = fields.One2many('oa.flow.step', 'step_lvid', string='流程步骤')
    oa_comment = fields.Char(string='备注')
    oa_ordertype = fields.Many2one('oa.ordertype', string='单子类型')

    # approvers = fields.Char(string='审批人')

    def getflowway(self, vals):
        '''简单的获取流程'''
        flowways = self.env['oa.flow'].search([('oaflow_flowtype', '=', self.oa_ordertype.id)])
        self.oa_flowway = flowways
        flowwaylines2 = self.env['oa.flow.line.content']
        for line in flowways.oaflow_lines:
            # 判断此流程行是否有条件限制，如果有，在进行判断是否符合，如果不符合则删除
            if line.condivalue:
                domain = eval(line.condivalue)
                order = self.env[self.oa_ordertype.model_name.model].search(domain)
                if order:
                    fieldname = 'x_oa_%s_docname' % (str.lower(self.oa_ordertype.sequence_prefix))
                    if vals.get(fieldname) in order._ids:
                        data = {
                            'line_lvcid': self.id,
                            'approvalnumber': line.approvalnumber,
                            'positer_desc': line.positer_desc,
                            'department_id': line.department_id,
                            'positer_id': line.positer_id,
                            'isteamapproval': line.isteamapproval,
                            'candidate_ids': line.candidate_ids,
                        }
                        new_line = flowwaylines2.new(data)
                        flowwaylines2 += new_line
            else:
                data = {
                    'line_lvcid': self.id,
                    'approvalnumber': line.approvalnumber,
                    'positer_desc': line.positer_desc,
                    'department_id': line.department_id,
                    'positer_id': line.positer_id,
                    'isteamapproval': line.isteamapproval,
                    'candidate_ids': line.candidate_ids,
                }
                new_line = flowwaylines2.new(data)
                flowwaylines2 += new_line
        self.oa_flowwaylines = flowwaylines2

    def get_candidate(self):
        '''获取候选人'''
        if self.oa_flowwaylines:
            # 获取申请人的所有信息
            candidata = self.env['hr.employee'].search([('name', '=', self.oa_applicant.name)])
            for line in self.oa_flowwaylines:
                canids = []
                # 没有部门且不是团队审批的情况（只有岗位审批）
                if not line.department_id and line.isteamapproval != '0' and not line.candidate_ids and line.positer_id:
                    # 获取当前申请人所在部门（有可能在两个部门）
                    # cand_ids = candidata.department_ids._ids
                    if line.approvalnumber == 'p0':
                        if candidata.job_id == line.positer_id or line.positer_id.name == '普工':
                            caninfo = self.env['hr.employee'].search(
                                [('id', '=', candidata.id)])
                            canids.append(caninfo.id)
                            line.write({
                                'line_lvcid': self.id,
                                'candidate_ids': [[6, 0, canids]]
                            })
                        else:
                            raise osv.except_osv("您不是" + line.positer_id.name + ",没有权限！")
                    else:
                        # 获取部门ID相同的人
                        cans = self.env['hr.employee']
                        cans2 = self.env['hr.employee']
                        for did in candidata.department_id._ids:
                            for item in self.env['hr.employee'].search([('department_id', '=', did)]):
                                if item not in cans:
                                    cans += item
                        for can in cans:
                            # 部门里有相关的岗位即使用此岗位人员，若无此岗位则直接岗位搜索确定人员
                            if line.positer_id.id in can.job_id.ids:
                                cans2 += can
                                canids.append(can.id)
                                continue
                            else:
                                for c in self.env['hr.employee'].search([('job_id', '=', line.positer_id.id)]):
                                    if c not in cans2:
                                        cans2 += c
                                        canids.append(c.id)

                        line.write({
                            'line_lvcid': self.id,
                            'candidate_ids': [[6, 0, canids]]
                        })
                # 没有岗位且不是团队审批的情况（只有部门审批）
                elif not line.positer_id and line.isteamapproval != '0' and not line.candidate_ids and line.department_id:
                    # 获取部门ID
                    dpid = line.department_id.id
                    if line.approvalnumber == 'p0':
                        if candidata.department_id == line.department_id:
                            caninfos = self.env['hr.employee'].search([('department_id', '=', dpid)])
                            for canid in caninfos:
                                canids.append(canid.id)
                            line.write({
                                'line_lvcid': self.id,
                                'candidate_ids': [[6, 0, canids]]
                            })
                        else:
                            raise osv.except_osv("您不是" + line.department_id.name + "人员,没有权限！")
                    else:
                        if len(self.env['hr.employee'].search([('department_id', '=', dpid)])) == 1:
                            candidate_ids = self.env['hr.employee'].search([('department_id', '=', dpid)])
                        else:
                            candidate_ids = self.env['hr.employee'].search([('department_id', '=', dpid)])
                        for canid in candidate_ids:
                            canids.append(canid.id)

                        line.write({
                            'line_lvcid': self.id,
                            'candidate_ids': [[6, 0, canids]]
                        })
                # 没有岗位和部门的情况（只有团队审批）
                elif not line.department_id and not line.positer_id and line.isteamapproval == '0' and not line.candidate_ids:
                    # 获取管理员姓名
                    adminname = self.env['hr.employee'].search([('name', '=', candidata.name)]).parent_id

                    canids.append(adminname.id)
                    line.write({
                        'line_lvcid': self.id,
                        'candidate_ids': [[6, 0, canids]]
                    })
                # 只要候选人有人，那就不需要操作
                elif not line.department_id and not line.positer_id and line.isteamapproval != '0' and line.candidate_ids:

                    for canid in line.candidate_ids:
                        canids.append(canid.id)
                    line.write({
                        'line_lvcid': self.id,
                        'candidate_ids': [[6, 0, canids]]
                    })
                # 全部为空的情况
                elif not line.department_id and not line.positer_id and not line.isteamapproval and not line.candidate_ids:

                    canids.append(self.env['hr.employee'].search([('id', '=', candidata.id)]).id)
                    line.write({
                        'line_lvcid': self.id,
                        'candidate_ids': [[6, 0, canids]]
                    })
                # 岗位和部门都有的情况
                elif line.department_id and line.positer_id:
                    # 获取部门ID
                    dpid = line.department_id.id
                    # 获取岗位ID
                    pid = line.positer_id.id

                    canids.append(self.env['hr.employee'].search(
                        [('department_id', '=', dpid), ('job_id', '=', pid)]).id)
                    line.write({
                        'line_lvcid': self.id,
                        'candidate_ids': [[6, 0, canids]]
                    })

                # 岗位有，同时是团队审批的情况
                elif line.positer_id and line.isteamapproval == '0':
                    # 获取部门ID
                    dpid = candidata.department_id.id
                    # 获取岗位ID
                    pid = line.positer_id.id

                    canids.append(self.env['hr.employee'].search(
                        [('department_id', '=', dpid), ('job_id', '=', pid)]).id)
                    line.write({
                        'line_lvcid': self.id,
                        'candidate_ids': [[6, 0, canids]]
                    })
            createtime = self.oa_createdate
            for line in self.oa_flowwaylines:
                ids = []
                ids += line.candidate_ids.ids
                for id in ids:
                    # 筛选流程行，并对流程委托表进行筛选
                    # caninfo = self.env['hr.employee'].browse(id)
                    entrustinfo = self.env['oa.entrust'].search(
                        [('et_type', 'ilike', self.oa_ordertype.id), ('et_from', '=', id),
                         ("et_start", "<=", createtime),
                         ("et_end", ">=", createtime)], limit=1)
                    if entrustinfo:
                        ids.remove(id)
                        ids.append(entrustinfo.et_to.id)
                candidate_ids = [(6, 0, ids)]
                line.write({
                    'candidate_ids': candidate_ids
                })

    def action_commit(self):
        '''
        提交单子
        :return:
        '''
        uname = self.env['res.users'].browse(self.env.uid).name
        uinfo = self.env['hr.employee'].search([('name', '=', uname)])
        if uinfo.id in self.oa_approver._ids:
            # 找到当前审批的步骤从1开始
            _index = int(0)
            _index = self._get_index(approver=uinfo, flowwaylines=self.oa_flowwaylines)
            newflowwaylines = self._change_positerState('1', index=_index)
            position = int(-1)
            # 总流程步骤-未完成的流程步骤=已完成的流程步骤
            # 当已完成的流程步骤=0时：单子状态为 待审批
            # 总流程步骤>当已完成的流程步骤>0时：单子状态为 审批ing
            # 当已完成的流程步骤=总流程步骤：单子状态为 完成
            if len(self.oa_flowwaylines) - len(newflowwaylines) == 0:
                self.update({
                    'oa_state': 'noapprove'
                })
            elif len(self.oa_flowwaylines) - len(newflowwaylines) > 0 and len(newflowwaylines) > 0:
                self.update({
                    'oa_state': 'approving'
                })
            elif len(self.oa_flowwaylines) == len(newflowwaylines):
                self.update({
                    'oa_state': 'ok'
                })
                # if self.ismarked == '1':
                #     self.env['oa.jingyuan'].search([('name', '=', self.mainorder)]).state = self.mainorderstate
            if len(newflowwaylines) == 1:
                self.oa_approver = newflowwaylines[0].candidate_ids
                self.oa_nextapprover = False
            else:
                for line in newflowwaylines:
                    position += 1
                    if position == 1:
                        self.oa_nextapprover = line.candidate_ids
                    elif position == 0:
                        self.oa_approver = line.candidate_ids
                        if self.oa_applicant.id in self.oa_nextapprover._ids and not line.positer_id and line.isteamapproval != '0' and not line.department_id:
                            # 说明这是一步需要自己完成的步骤，可能是填写，或是修改
                            if self.oa_ordertype == '2' or self.oa_ordertype == '5':
                                self.update({
                                    'oa_state': 'editing'
                                })
            if not self.oa_ordertype.isother_mode:
                mainactivity = self.env['mail.activity'].search([('res_model', '=', 'oa'), ('res_id', '=', self.id)])
                if mainactivity:
                    mainactivity.action_done()
            else:
                base_id = self.env[self.oa_ordertype.model_name.model].search(
                    [('x_oa_resourceflow', '=', self.id)]).id
                mainactivity = self.env['mail.activity'].search(
                    [('res_model', '=', self.oa_ordertype.model_name.model), ('res_id', '=', base_id)])
                if mainactivity:
                    mainactivity.action_done()

            self._set_flowway_step(_index - 1, '已提交')

            # 添加提交单据人员的管理员关注
            oa_info = self.env['oa'].search([('id', '=', self.id)])
            uname = self.env['res.users'].browse(self.env.uid).name
            uinfo = self.env['hr.employee'].search([('name', '=', uname)])
            employee_info = self.env['hr.employee'].search([('name', '=', uinfo.name)], limit=1)

            if employee_info.parent_id.id:
                manager_info = self.env['hr.employee'].search([('id', '=', employee_info.parent_id.id)], limit=1)
                manager_user = self.env['res.users'].search([('name', '=', manager_info.name)])

                mail_invite = self.env['mail.wizard.invite'].with_context({
                    'default_res_model': oa_info._name,
                    'default_res_id': self.id}).create({
                    'partner_ids': [(4, manager_user.partner_id.id)],
                    'send_mail': False,
                })
                mail_invite.add_followers()
        else:
            raise osv.except_osv('您没有权限提交此单据！')

    def action_approve_pass(self):
        '''
        审核通过
        :return:
        '''
        _index = int(0)
        uidapprover = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        _index = self._get_index(approver=uidapprover, flowwaylines=self.oa_flowwaylines)
        newflowwaylines = self._change_positerState('2', index=_index)
        position = int(-1)
        # 总流程步骤-未完成的流程步骤=已完成的流程步骤
        # 当已完成的流程步骤=0时：单子状态为 待审批
        # 总流程步骤>当已完成的流程步骤>0时：单子状态为 审批ing
        # 当已完成的流程步骤=总流程步骤：单子状态为 完成
        if len(self.oa_flowwaylines) - len(newflowwaylines) > 0 and len(newflowwaylines) > 0:
            self.update({
                'oa_state': 'approving'
            })
        elif len(newflowwaylines) == 0:
            self.update({
                'oa_state': 'ok'
            })
            # if self.ismarked == '1':
            #     self.env['oa.jingyuan'].search([('name', '=', self.mainorder)]).state = self.mainorderstate
        if len(newflowwaylines) == 1:
            self.oa_approver = newflowwaylines[0].candidate_ids
            self.oa_nextapprover = False
        else:
            for line in newflowwaylines:
                position += 1
                if position == 1:
                    self.oa_nextapprover = line.candidate_ids
                elif position == 0:
                    self.oa_approver = line.candidate_ids
                    if self.oa_applicant.id in self.oa_nextapprover._ids and not line.positer_id and line.isteamapproval != '0' and not line.department_id:
                        # 说明这是一步需要自己完成的步骤，可能是填写，或是修改
                        if self.oa_ordertype == '2' or self.oa_ordertype == '5':
                            self.update({
                                'oa_state': 'editing'
                            })
        self._set_flowway_step(_index - 1, '已通过')

    def action_approve_rejected(self):
        '''
        审核驳回
        :return:
        '''
        _index = int(0)
        uidapprover = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        _index = self._get_index(approver=uidapprover, flowwaylines=self.oa_flowwaylines)
        self._change_positerState('3', index=_index)
        _index -= 1
        if _index - 1 > 0:
            '''当单子处于被驳回但又未回到申请人手中时，单子的状态会修改为被驳回状态，提示上一审批人重新审核'''
            line = self.oa_flowwaylines[_index - 1]
            strname = line.candidate_ids
            self.oa_approver = strname
            if self.oa_approver.id == self.oa_applicant.id and not line.positer_id and line.isteamapproval != '0' and not line.department_id:
                # 说明这是一步需要自己完成的步骤，可能是填写，或是修改
                if self.oa_ordertype == '2' or self.oa_ordertype == '5':
                    self.update({
                        'oa_state': 'editing'
                    })
            else:
                self.update({
                    'oa_state': 'goback'
                })
        else:
            '''当单子回到申请人手中时，单子的状态会修改为草稿状态，提示申请人重新提交'''
            self.update({
                'oa_state': 'nosubmit'
            })
            self.oa_approver = self.env['hr.employee'].search([('name', '=', self.oa_applicant.name)])
        line2 = self.oa_flowwaylines[_index]
        strname2 = line2.candidate_ids
        self.oa_nextapprover = strname2
        self._set_flowway_step(_index, '驳回')

    def action_goback_to_approve(self):
        '''
        驳回至申请人
        :return:
        '''
        _index = int(0)
        '''当单子回到申请人手中时，单子的状态会修改为草稿状态，提示申请人重新提交'''
        self.update({
            'oa_state': 'goback'
        })
        # 重置流程行中执行状态
        for line in self.oa_flowwaylines:
            if line.positer_state:
                line.positer_state = ''
        self.oa_approver = self.env['hr.employee'].search([('name', '=', self.oa_applicant.name)])
        line2 = self.oa_flowwaylines[_index + 1]
        strname2 = line2.candidate_ids
        self.oa_nextapprover = strname2
        self._set_flowway_step(_index, '驳回至申请人')

    def action_approve_termination(self):
        '''
        审批终止,无审批人,申请人无条件终止
        :return:
        '''
        if self.oa_applicant.user_id.id == self.env.uid:
            self.oa_state = 'termination'
            self.oa_approver = ""
            if not self.oa_ordertype.isother_mode:
                mainactivity = self.env['mail.activity'].search([('res_model', '=', 'oa'), ('res_id', '=', self.id)])
                if mainactivity:
                    mainactivity.unlink()
            else:
                base_id = self.env[self.oa_ordertype.model_name.model].search(
                    [('x_oa_resourceflow', '=', self.id)]).id
                mainactivity = self.env['mail.activity'].search(
                    [('res_model', '=', self.oa_ordertype.model_name.model), ('res_id', '=', base_id)])
                if mainactivity:
                    mainactivity.unlink()
            _logger.warning('终止成功')

    def _get_index(self, approver, flowwaylines):
        '''
        传入当前审批人，找到单子进行的步骤
        :param approver:
        :return:
        '''
        position = int(0)
        for i in flowwaylines:
            position += 1
            if approver in i.candidate_ids and (not i.positer_state or i.positer_state == '3'):
                return int(position)

    def _get_indexs(self, approver, flowwaylines):
        '''
        传入当前审批人，找到单子候选人相同的步骤
        :param approver:
        :return:
        '''
        position = []
        index = int(0)
        for i in flowwaylines:
            index += 1
            if approver in i.candidate_ids and (not i.positer_state or i.positer_state == '3'):
                position.append(index)
                return position

    def _change_positerState(self, state, index):
        '''
        通过不同的按钮，改变每个阶段的状态
        :param state: 1（已提交）、2（已通过）、3（已驳回）
        :return:
        '''
        # 存放重新获取需要继续的流程步骤
        flowwaylines3 = self.env['oa.flow.line.content']
        positer_state = state
        position = int(0)
        position2 = int(0)
        if state == "3":
            '''如果是驳回操作，那就要删除前一人流程行的操作状态'''
            self.oa_flowwaylines[index - 2].write({
                'positer_state': ""
            })
            # 获取需要删除操作状态 的流程行 的候选人
            approval2 = self.oa_flowwaylines[index - 2].candidate_ids
            if self.oa_flowway.oaflow_passapprove == '1':
                for line in self.oa_flowwaylines:
                    position += 1
                    # 判断流程中是否有相同审批人但却处于不同职位的都需要删除流程操作状态
                    if approval2 == line.candidate_ids and line.positer_state:
                        self.oa_flowwaylines[position - 1].write({
                            'positer_state': ""
                        })

        # 记录下当前审批人的对象，用作判断流程中是否有相同审批人但却处于不同职位的
        approval = self.oa_flowwaylines[index - 1].candidate_ids
        self.oa_flowwaylines[index - 1].write({
            'positer_state': positer_state
        })
        if self.oa_flowway.oaflow_passapprove == '1':
            for line in self.oa_flowwaylines:
                position2 += 1
                # 判断流程中是否有相同审批人但却处于不同职位的
                if approval == line.candidate_ids:
                    if line.approvalnumber != 'p0' and positer_state != '3':
                        positer_state = "2"
                    self.oa_flowwaylines[position2 - 1].write({
                        'positer_state': positer_state
                    })
        # 标记关联单子
        # self._seteditmark()
        # 重新获取需要继续的流程步骤
        for line in self.oa_flowwaylines:
            if not line.positer_state or line.positer_state == '3':
                flowwaylines3 += line
        return flowwaylines3

    def _set_flowway_step(self, position, operatstate):
        '''
        设置操作步骤详情
        :param step_name:
        :param operator:
        :param operatingresult:
        :param operatingtime:
        :param operatingdesc:
        :return:
        '''

        step_name = self.oa_flowway.oaflow_lines[position].positer_desc
        operator = self.env['hr.employee'].search(
            [('name', '=', self.env['res.users'].browse(self.env.uid).name)])
        if not operator:
            raise osv.except_osv('请在员工处添加此人！')
        else:
            operatorname = operator.name
        operatingresult = operatstate
        operatingtime = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        operatingdesc = self.oa_comment
        self.env['oa.flow.step'].create({
            'step_lvid': self.id,
            'step_name': step_name,
            'operator': operatorname,
            'operatingresult': operatingresult,
            'operatingtime': operatingtime,
            'operatingdesc': operatingdesc
        })
        self.oa_comment = ""
        # self.set_oa_state()
        if self.oa_state != 'ok':
            self.set_chatter_message(operator=operatorname, operationtime=operatingtime,
                                     operationresult=operatingresult,
                                     operationdesc=operatingdesc)

    def set_chatter_message(self, operator, operationtime, operationresult, operationdesc):
        '''
        自定义消息，显示在在线聊天
        :param operator:
        :param operationtime:
        :param operationresult:
        :param operationdesc:
        :return:
        '''
        if not operationdesc:
            operationdesc = ''
        name = ''
        index = 1
        for approv in self.oa_approver:
            name += approv.display_name
            if index < len(self.oa_approver):
                name += "、"
                index += 1
        self.message_post(body='''<ul><li>操作时间：%s</li>
                                    <li>操作人：%s</li>
                                    <li>操作结果：%s</li>
                                    <li>处理意见：<font color='red'>%s</font></li>
                                    <li>下一级审批人：%s</li>
                                    </ul>''' % (
            operationtime, operator, operationresult, operationdesc, name))

        '''
        自动添加安排给下一级审批人(使用OA流程单据作为通知单)
        '''
        if not self.oa_ordertype.isother_mode:
            # 判断是否是基础表单审批模式，如果是则添加由系统提示基础单据需要审批，否则默认为流程单据审批
            for approver in self.oa_approver:
                self.env['mail.activity'].create({
                    'res_model_id': self.env.ref('flowmanager.model_oa').id,
                    'res_id': self.id,
                    'user_id': approver.user_id.id,
                    'activity_type_id': self.env['mail.activity.type'].search([('name', '=', '审批')]).id,
                    'summary': '审批',
                    'date_deadline': datetime.datetime.now(),
                })

        '''
        自动添加安排给下一级审批人(使用基础单据作为通知单)
        '''
        for approver in self.oa_approver:
            next_approver_user_info = self.env['res.users'].search([('name', '=', approver.display_name)])
            next_approver_partner_id = next_approver_user_info.partner_id.id
            '''
            自动添加安排给下一级审批人(使用基础单据作为通知单) 如果不进行活动安排，则需要给基础单据添加关注者
            '''
            if self.oa_ordertype.isother_mode:
                res_model_id = self.env['ir.model'].search([('model', '=', self.oa_ordertype.model_name.model)])
                current_recipt_id = self.env[self.oa_ordertype.model_name.model].search(
                    [('x_oa_resourceflow', '=', self.id)]).id
                if current_recipt_id:
                    self.env['mail.activity'].create({
                        'res_model_id': res_model_id.id,
                        'res_id': current_recipt_id,
                        'user_id': approver.user_id.id,
                        'activity_type_id': self.env['mail.activity.type'].search([('name', '=', '审批')]).id,
                        'summary': '审批',
                        'date_deadline': datetime.datetime.now(),
                    })
                else:
                    raise  osv.except_osv('如果开启了基础表单审批模式，请在基础表单动作按钮处点击【提交审批】')
            else:
                mail_invite = self.env['mail.wizard.invite'].with_context({
                    'default_res_model': self.oa_ordertype.model_name.model,
                    'default_res_id': current_recipt_id}).create({
                    'partner_ids': [(4, next_approver_partner_id)], 'send_mail': False})
                mail_invite.add_followers()


    @api.model
    def create(self, vals):
        '''
        创建请假单开始进入状态位变化阶段（notsubmit=草稿，noapprove=待审批，approving=审批中，ok=完成）
        :param vals:
        :return:
        '''

        ordertype = self.env['oa.ordertype'].search([('id', '=', vals.get('oa_ordertype'))])
        typename = ordertype.name
        newformname = self.env['ir.sequence'].search([('name', '=', typename)]).next_by_id()
        vals.setdefault('oa_name', newformname)
        vals.setdefault('oa_state', 'nosubmit')
        oa_order = super(oa, self).create(vals)
        oa_order.getflowway(vals)
        oa_order.get_candidate()
        a = int(0.0)
        for line in oa_order.oa_flowwaylines:
            a += 1
            if a == 1:
                oa_order.update({
                    'oa_approver': [[6, 0, line.candidate_ids._ids]]
                })
            elif a == 2:
                oa_order.update({
                    'oa_nextapprover': [[6, 0, line.candidate_ids._ids]]
                })
        # # 1、获取当前流程单类型的信息
        # ordertypeinfo = self.env['oa.ordertype'].search([('code', '=', oa_order.oa_ordertype)])
        # # 2、获取此类型的使用模型
        # current_res_model = ordertypeinfo.model_name
        # # 3、获取流程单内使用此模型的字段
        # fieldname = self.env['ir.model.fields'].search(
        #     [('model', '=', 'oa'), ('relation', '=', current_res_model)]).name
        #
        # sql = "SELECT " + fieldname + " FROM oa WHERE id='" + str(oa_order.id) + "'"
        # self._cr.execute(sql)
        # baseorderid = self._cr.fetchall()
        # current_recipt_id = baseorderid[0][0]
        # baseorder = self.env[current_res_model].browse(current_recipt_id)
        # baseorder.resourceflow = oa_order.id
        return oa_order

    def write(self, vals):
        if not self.oa_name:
            ordertype = self.env['oa.ordertype'].search([('code', '=', self.oa_ordertype)])
            typename = ordertype.name
            newformname = self.env['ir.sequence'].search([('name', '=', typename)]).next_by_id()
            vals.setdefault('oa_name', newformname)
        # 筛选申请人为当前用户，同时流程单状态为草稿
        # json_str = simplejson.dumps(vals)
        # if json_str.find("docname") >= 0:
        #     raise osv.except_osv('基本单据不可修改！')
        return super(oa, self).write(vals)

    def unlink(self):
        morder = self.env['mail.activity'].search([('res_name', '=', self.oa_name)])
        d = {'dbcname': self._cr.dbname, 'contentkey': morder.id}
        r = requests.post("http://www.yiyuntong.com/mobile/phone/odoo/message/deleteUsermessage", d)
        morder.unlink()
        _logger.warning('删除成功')
        return super(oa, self).unlink()

    def action_approval(self):
        # 批准事件
        uname = self.env['res.users'].browse(self.env.uid).name
        uinfo = self.env['hr.employee'].search([('name', '=', uname)])
        if uinfo.id in self.oa_approver._ids:
            if not self.oa_ordertype.isother_mode:
                mainactivity = self.env['mail.activity'].search([('res_model', '=', 'oa'), ('res_id', '=', self.id)])
                if mainactivity:
                    mainactivity.action_done()
            else:
                base_id = self.env[self.oa_ordertype.model_name.model].search(
                    [('x_oa_resourceflow', '=', self.id)]).id
                mainactivity = self.env['mail.activity'].search(
                    [('res_model', '=', self.oa_ordertype.model_name.model), ('res_id', '=', base_id)])
                if mainactivity:
                    mainactivity.action_done()
            # 1、获取当前流程单类型的信息
            ordertypeinfo = self.env['oa.ordertype'].search([('id', '=', self.oa_ordertype.id)])
            # 2、获取此类型的使用模型
            current_res_model = ordertypeinfo.model_name.model
            # 3、获取流程单内使用此模型的字段
            fieldname = self.env['ir.model.fields'].search(
                [('model', '=', 'oa'), ('relation', '=', current_res_model)]).name

            sql = "SELECT " + fieldname + " FROM oa WHERE id='" + str(self.id) + "'"
            self._cr.execute(sql)
            baseorderid = self._cr.fetchall()
            current_recipt_id = baseorderid[0][0]
            baseorder = self.env[current_res_model].browse(current_recipt_id)
            mainactivitys2 = self.env['mail.activity'].search(
                [('res_name', '=', baseorder.name)])
            for mainactivity in mainactivitys2:
                mainactivity.action_done()
            self.action_approve_pass()
        else:
            raise osv.except_osv('当前审批人不是你！')

    def action_sure(self):
        # 驳回确认时触发事件
        uname = self.env['res.users'].browse(self.env.uid).name
        uinfo = self.env['hr.employee'].search([('name', '=', uname)])
        if uinfo.id in self.oa_approver._ids:
            if not self.oa_ordertype.isother_mode:
                mainactivity = self.env['mail.activity'].search([('res_model', '=', 'oa'), ('res_id', '=', self.id)])
                if mainactivity:
                    mainactivity.action_done()
            else:
                base_id = self.env[self.oa_ordertype.model_name.model].search(
                    [('x_oa_resourceflow', '=', self.id)]).id
                mainactivity = self.env['mail.activity'].search(
                    [('res_model', '=', self.oa_ordertype.model_name.model), ('res_id', '=', base_id)])
                if mainactivity:
                    mainactivity.action_done()
            self.action_approve_rejected()
        else:
            raise osv.except_osv('当前审批人不是你！')

    def get_oa_flowway(self, type):
        '''
        选择流程
        :return:
        '''
        flowways = self.env['oa.flow'].search([('oaflow_flowtype', '=', type)])
        self.oa_flowway = flowways
        flowwaylines2 = self.env['oa.flow.line.content']
        for line in self.oa_flowway.oaflow_lines:
            data = {
                'line_cid': self.id,
                'approvalnumber': line.approvalnumber,
                'positer_desc': line.positer_desc,
                'department_id': line.department_id,
                'positer_id': line.positer_id,
                'isteamapproval': line.isteamapproval,
                'candidate_ids': line.candidate_ids,
            }
            new_line = flowwaylines2.new(data)
            flowwaylines2 += new_line
        self.oa_flowwaylines = flowwaylines2

    def otherorder_commit(self):
        otherorder = self.env.context.get('active_id')
        otherorder_model = self.env.context.get('active_model')
        omodel = self.env['ir.model'].search([('model', '=', otherorder_model)])
        ordertype = self.env['oa.ordertype'].search([('model_name', '=', omodel.id)])
        typename = ordertype.name
        newformname = self.env['ir.sequence'].search([('name', '=', typename)]).next_by_id()
        fieldname = 'x_oa_%s_docname' % (str.lower(ordertype.sequence_prefix))
        res = {
            'oa_application': self.env['hr.employee'].search([('name', '=', self.env.user.name)]).id,
            fieldname: otherorder,
            'oa_name': newformname,
            'oa_state': 'nosubmit',
            'oa_ordertype': ordertype.id,
        }
        order = self.env['oa'].create(res)
        baseorder = self.env[otherorder_model].browse(otherorder)
        baseorder.update({
            'x_oa_resourceflow': order.id
        })
        order.action_commit()


# class mail_activity(models.Model):
#     _inherit = 'mail.activity'
#
#
#     def action_apporval(self):
#         if self.env.uid == self.user_id.id:
#             # 3、获取流程单内使用此模型的字段
#             fieldname = self.env['ir.model.fields'].search(
#                 [('model', '=', 'oa'), ('relation', '=', self.res_model)]).name
#             oa_order = self.env['oa'].search([(fieldname, '=', self.res_id)])
#             oa_order.oa_comment = self.note
#             MailActivity.action_done(self)
#             oa_order.action_approve_pass()
#         else:
#             raise osv.except_osv('当前审批人不是你！')
#
#
#     def action_refuse(self):
#         if self.env.uid == self.user_id.id:
#             if self.note:
#                 # 3、获取流程单内使用此模型的字段
#                 fieldname = self.env['ir.model.fields'].search(
#                     [('model', '=', 'oa'), ('relation', '=', self.res_model)]).name
#                 oa_order = self.env['oa'].search([(fieldname, '=', self.res_id)])
#                 oa_order.oa_comment = self.note
#                 MailActivity.action_done(self)
#                 oa_order.action_approve_rejected()
#             else:
#                 raise osv.except_osv('请填写处理意见！')
#         else:
#             raise osv.except_osv('当前审批人不是你！')
#
#
#     def action_refuse_to_approve(self):
#         '''
#         驳回至申请人
#         :return:
#         '''
#         if self.env.uid == self.user_id.id:
#             if self.note:
#                 # 3、获取流程单内使用此模型的字段
#                 fieldname = self.env['ir.model.fields'].search(
#                     [('model', '=', 'oa'), ('relation', '=', self.res_model)]).name
#                 oa_order = self.env['oa'].search([(fieldname, '=', self.res_id)])
#                 oa_order.oa_comment = self.note
#                 MailActivity.action_done(self);
#                 oa_order.action_goback_to_approve()
#             else:
#                 raise osv.except_osv('请填写处理意见！')
#         else:
#             raise osv.except_osv('当前审批人不是你！')


class oa_ordertype(models.Model):
    _name = 'oa.ordertype'
    _order = 'code desc'

    name = fields.Char(string='类型名称', help='为你的单据类型命名')
    code = fields.Char(string='类型编号', help='为1、2、3、4……顺序')
    model_name = fields.Many2one('ir.model', string='模型名称', help='单据关联的模型')
    sequence_prefix = fields.Char('序列前缀', help='为你的单据编号设置前缀')
    padding = fields.Integer('序列大小', help='为你的编号设置位数，前缀除外', default=6)
    ir_sequence_id = fields.Many2one('ir.sequence', string='序列ID')
    model_view = fields.Many2one('ir.ui.view', string='模型视图', help="单据关联的模型的主要视图（您要关联的界面）")
    isother_mode = fields.Boolean(string='是否为基础表单审批模式', default=False,
                                  help='用于判断是否是基础表单审批模式，如果是则添加由系统提示基础单据需要审批，否则默认为流程单据审批')
    create_menu = fields.Char('创建菜单', help='创建菜单时增加的参数 如 "ir.ui.view:1," ')
    start_others_mode = fields.Char('开启其他模式审批', help='在开启其他模式审批时增加的参数 如 "ir.ui.view:1," ')

    @api.onchange('model_name')
    def _onchange_model_name(self):
        res = {
            'domain': {'model_view': [('model', '=', self.model_name.model)]},
        }
        return res

    @api.model
    def create(self, vals):
        order = super(oa_ordertype, self).create(vals)
        sequence = self.env['ir.sequence'].create({
            'name': order.name,
            'prefix': order.sequence_prefix,
            'padding': order.padding
        })
        order.update({
            'ir_sequence_id': sequence.id
        })
        return order

    def write(self, vals):
        if 'isother_mode' in vals:
            isother_mode = vals.get('isother_mode')
            if not isother_mode:
                for map in str(self.start_others_mode).split(';'):
                    key = map.split(',')[0]
                    value = map.split(',')[1]
                    ord = self.env[key].search([('id', '=', int(value))])
                    if ord:
                        ord.unlink()
        order = super(oa_ordertype, self).write(vals)
        if self.ir_sequence_id:
            self.ir_sequence_id.write({
                'name': self.name,
                'prefix': self.sequence_prefix,
                'padding': self.padding
            })
        else:
            self.env['ir.sequence'].create({
                'name': self.name,
                'prefix': self.sequence_prefix,
                'padding': self.padding
            })
        return order

    def unlink(self):
        if self.create_menu:
            for map in str(self.create_menu).split(';'):
                key = map.split(',')[0]
                value = map.split(',')[1]
                ord = self.env[key].search([('id', '=', int(value))])
                if ord:
                    ord.unlink()

        if self.start_others_mode:
            for map in str(self.start_others_mode).split(';'):
                key = map.split(',')[0]
                value = map.split(',')[1]
                ord = self.env[key].search([('id', '=', int(value))])
                if ord:
                    ord.unlink()

        self.env['ir.sequence'].browse(self.ir_sequence_id.id).unlink()
        return super(oa_ordertype, self).unlink()

    def action_create_menu(self):
        if not self.create_menu:
            # 创建菜单时的参数
            param = "ir.ui.menu,%d;ir.actions.act_window,%d;ir.ui.view,%d;ir.model.fields,%d"

            search_view_id = self.env['ir.ui.view'].search(
                [('model', '=', 'oa'), ('name', '=', '流程单筛选'), ('type', '=', 'search')])
            # 首先生成action
            act_id = self.env['ir.actions.act_window'].sudo().create({
                'name': self.name.replace("单", "") + "流程",
                'type': 'ir.actions.act_window',
                'binding_type': 'action',
                'domain': "[('oa_ordertype', '=', %d),('message_partner_ids.user_ids.id', 'parent_of', uid)]" % (
                    self.id),
                'context': "{'default_oa_ordertype' : %d,'search_default_my_approvering':1}" % (self.id),
                'res_model': 'oa',
                'target': 'current',
                'view_model': 'tree,form',
                'search_view_id': search_view_id.id,
            })
            # 获取上级菜单
            # 再则生成menu
            sql = "select id from ir_ui_menu where name ='流程单'"
            self._cr.execute(sql)
            menu_parent_id = self._cr.dictfetchall()[0].get('id')
            menu_action = 'ir.actions.act_window,%d' % (act_id)
            menu_id = self.env['ir.ui.menu'].sudo().create({
                'name': self.name.replace("单", "") + "流程",
                'parent_id': menu_parent_id,
                'action': menu_action,
                'sequence': self.code
            })

            # 最后要修改原来界面，增加相关字段
            # 增加字段信息
            fieldname = 'x_oa_%s_docname' % (str.lower(self.sequence_prefix))
            model_id = self.env['ir.model'].search([('model', '=', 'oa')])
            field_id = self.env['ir.model.fields'].sudo().create({
                'name': fieldname,
                'model': 'oa',
                'relation': self.model_name.model,
                'model_id': model_id.id,
                'field_description': self.name,
                'ttype': 'many2one',
            })
            # 获取继承视图
            inherit_id = self.env['ir.ui.view'].search(
                [('model', '=', 'oa'), ('name', '=', 'base流程表单'), ('type', '=', 'form')])
            arch_db = '''<?xml version="1.0"?>
               <xpath expr="//group[@name='oa_otherinfo']" position="inside">
                    <field name="%s" attrs="{'invisible': [('oa_ordertype', 'not in', [%d])],'readonly':[('oa_state','not in',['nosubmit', False])]}"/>
               </xpath>''' % (fieldname, self.id)
            view_id = self.env['ir.ui.view'].sudo().create({
                'name': self.name.replace("单", "") + "表单",
                'model': 'oa',
                'type': 'form',
                'arch_db': arch_db,
                'arch_fs': '',
                'inherit_id': inherit_id.id,
            })
            param = param % (menu_id, act_id, view_id, field_id)
            self.update({
                'create_menu': param
            })

    def action_start_others_mode(self):
        if not self.start_others_mode:
            # 创建菜单时的参数
            param = "ir.actions.server,%d;ir.actions.server,%d;ir.actions.server,%d;ir.ui.view,%d;ir.model.fields,%d;ir.model.fields,%d"
            if not self.isother_mode:
                self.isother_mode = True
            if self.isother_mode:
                # 首先添加两个字段
                re_field = self.env['ir.model.fields'].search(
                    [('name', '=', 'x_oa_resourceflow'), ('model', '=', self.model_name.model)])
                st_field = self.env['ir.model.fields'].search(
                    [('name', '=', 'x_oa_state'), ('model', '=', self.model_name.model)])
                if not re_field:
                    fieldname = 'x_oa_resourceflow'
                    field_id1 = self.env['ir.model.fields'].sudo().create({
                        'name': fieldname,
                        'model': self.model_name.model,
                        'relation': 'oa',
                        'model_id': self.model_name.id,
                        'field_description': '源流程',
                        'ttype': 'many2one',
                    })
                if not st_field:
                    fieldname = 'x_oa_state'
                    field_id2 = self.env['ir.model.fields'].sudo().create({
                        'name': fieldname,
                        'model': self.model_name.model,
                        'related': 'x_oa_resourceflow.oa_state',
                        'model_id': self.model_name.id,
                        'field_description': '源流程状态',
                        'ttype': 'selection',
                        'selection': "[('nosubmit', '草稿'),('noapprove', '待审批'),('approving', '审批中'),('ok', '完成'), ('goback', '被驳回'), ('editing', '编辑中'), ('termination', '终止')]",
                    })
                    # 其次在添加布局
                    # '''<xpath expr="//header" position="inside">
                    #      <button name="%(flowmanager.action_othermode_commit)d" string="提交审批" type="action" class="oe_highlight"
                    #          attrs="{'invisible': ['|',('x_oa_state', 'not in', ['nosubmit','',False])]}"/>
                    #      <button name="%(flowmanager.action_othermode_approve)d" string="批准" type="action" class="oe_highlight"
                    #              attrs="{'invisible': ['|',('x_oa_state', 'not in', ['noapprove','approving','goback','editing'])]}"/>
                    #      <button name="%(flowmanager.action_othermode_reject)d" string="驳回" type="action"
                    #              class="oe_highlight"
                    #              attrs="{'invisible': ['|',('x_oa_state', 'not in', ['noapprove','approving','goback'])]}"/>
                    #      <button name="%(flowmanager.action_othermode_over)d" string="审批终止" type="action" class="oe_highlight"
                    #              attrs="{'invisible': ['|',('x_oa_state', 'not in', ['noapprove','approving','goback','editing'])]}"/>
                    # </xpath>'''
                arch_db = '''<?xml version="1.0"?><data>
                    <xpath expr="//sheet" position="inside">
                         <field name="x_oa_resourceflow" readonly="1"/>
                         <field name="x_oa_state" readonly="1"/>
                    </xpath>
                    <xpath expr="//header" position="inside">
                             <button name="%(action_oa_step)d" string="驳回" type="action"
                                     class="oe_highlight"
                                     attrs="{'invisible': ['|',('x_oa_state', 'not in', ['noapprove','approving','goback'])]}"/>
                    </xpath>
                </data>'''
                # 获取继承视图
                inherit_id = self.env['ir.ui.view'].search([('id', '=', self.model_view.id)])
                view_id = self.env['ir.ui.view'].sudo().create({
                    'name': self.model_view.name,
                    'model': self.model_name.model,
                    'type': self.model_view.type,
                    'arch_db': arch_db,
                    'arch_fs': '',
                    'inherit_id': inherit_id.id,
                })
                # 最后为添加的按钮 加上执行方法
                model_id = self.env['ir.model'].search([('model', '=', 'oa')])
                # 'model_' + str(self.model_name.model).replace('.', "_")
                act_id1 = self.env['ir.actions.server'].sudo().create({
                    'name': "提交审批",
                    'type': 'ir.actions.server',
                    'model_id': model_id.id,
                    'binding_model_id': self.model_name.id,
                    'state': 'code',
                    'code': 'model.otherorder_commit()',
                })
                act_id2 = self.env['ir.actions.server'].sudo().create({
                    'name': "批准",
                    'type': 'ir.actions.server',
                    'model_id': model_id.id,
                    'binding_model_id': self.model_name.id,
                    'state': 'code',
                    'code': 'model.action_approval()',
                })
                act_id3 = self.env['ir.actions.server'].sudo().create({
                    'name': "审批终止",
                    'type': 'ir.actions.server',
                    'model_id': model_id.id,
                    'binding_model_id': self.model_name.id,
                    'state': 'code',
                    'code': 'model.action_approve_termination()',
                })
                param = param % (act_id1, act_id2, act_id3, view_id, field_id1, field_id2)
                self.update({
                    'start_others_mode': param
                })


class oa_batch_substitution(models.Model):
    _name = 'oa.batch.substitution'

    substitution_user = fields.Many2one('res.users', string='代批人员')

    # 批量待批
    def batch_substitution(self):
        # 获取选中的OA单据
        oa_flows = self.env['oa'].browse(self.env.context.get('active_ids', False))

        # 确认选中的流程，当前审批人是当前用户，否则弹出警告
        for oa_flow in oa_flows:
            username = self.env['res.users'].browse(self.env.uid).name
            user_employee = self.env['hr.employee'].search([('name', '=', username)])
            if not (user_employee.id in oa_flow.oa_approver._ids) or oa_flow in ('nosubmit', 'ok'):
                raise osv.except_osv('请检查选择的流程！')

        # 确认代批人员已选择
        if not self.substitution_user:
            raise osv.except_osv('请选择代批人员！')

        for oa_flow in oa_flows:
            # 添加代批人员关注
            substitution_user_info = self.env['res.users'].search([('id', '=', self.substitution_user.id)])
            mail_invite = self.env['mail.wizard.invite'].with_context({
                'default_res_model': oa_flow._name,
                'default_res_id': oa_flow.id}).create({
                'partner_ids': [(4, substitution_user_info.partner_id.id)],
                'send_mail': False})
            mail_invite.add_followers()

            # 将对应的活动安排给代批人员
            activity = self.env['mail.activity'].search(
                [('res_name', '=', oa_flow.oa_name),
                 ('res_model_id', '=', self.env.ref('flowmanager.model_oa').id)])
            activity.write({'user_id': self.substitution_user.id})

            # 修改流程（审批人替换为代批人员）
            substitution_user_employee = self.env['hr.employee'].search([('name', '=', substitution_user_info.name)])

            new_ids = []
            new_ids.append(substitution_user_employee.id)

            positions = oa_flow._get_indexs(oa_flow.oa_approver, oa_flow.oa_flowwaylines)
            i = int(-1)
            for index in positions:
                i += 1
                current_line = oa_flow.oa_flowwaylines[index - 1]
                current_line.write({'candidate_ids': [(6, 0, new_ids)]})
                if i == 0 and positions[1] - 1 == index:
                    # 表示当前审批人和下级审批人是同一人
                    oa_flow.write({'oa_nextapprover': [(6, 0, new_ids)]})

            oa_flow.write({'oa_approver': [(6, 0, new_ids)]})
            # 添加人员代批消息
            operate_time = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
            oa_flow.message_post(body='''<ul>
                                            <li>操作时间：%s</li>
                                            <li>操作人：%s</li>
                                            <li>代批流程步骤：<font color='red'>%s</font></li>
                                            <li>代批人员：<font color='red'>%s</font></li>
                                         </ul>''' % (
                operate_time, username, current_line.positer_desc, substitution_user_info.name))
