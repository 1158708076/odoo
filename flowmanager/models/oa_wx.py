# -*- coding:utf-8 -*-
import base64
from io import BytesIO

import qrcode

from odoo import models, fields, api, _, exceptions
import http.client
import json


class oa_wx(models.Model):
    _name = 'oa.wx'
    _description = "微信公众号配置"
    _rec_name = 'name'

    name = fields.Char(string="公众号名称")
    appid = fields.Char(string="appid")
    secret = fields.Char(string="secret")
    access_token = fields.Char(string="Token")
    expires_in = fields.Char(string="定时时长")
    wx_state = fields.Boolean(string="启用", default=False)
    cron_order = fields.Many2one('ir.cron', string="相关任务")
    baseurl = fields.Char(string="对外域名", help="用于微信端消息连接的域名")

    def get_wx_access_token(self):
        '''获取微信公众号Access token'''
        if not self:
            self = self.env['oa.wx'].search([('wx_state', '=', True)], limit=1)
        conn = http.client.HTTPSConnection("api.weixin.qq.com")
        payload = ''
        headers = {}
        conn.request("GET",
                     "/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s" % (self.appid, self.secret),
                     payload, headers)
        res = conn.getresponse()
        data = res.read()
        result = data.decode("utf-8")
        jsonstr = json.loads(result)
        self.access_token = jsonstr['access_token']
        self.expires_in = jsonstr['expires_in']
        # 创建定时
        model_id = self.env['ir.model'].search([('model', '=', self._name)])
        if not self.cron_order:
            self.cron_order = self.env['ir.cron'].create({
                'name': '微信Access Token',
                'model_id': model_id.id,
                'state': 'code',
                'code': 'model.get_wx_access_token()',
                'interval_number': 115,
                'interval_type': 'minutes',
                'numbercall': 1,
                'doall': False,
            })


class msg_templete(models.Model):
    _name = 'msg.templete'
    _description = '消息记录'
    _rec_name = 'oa_order'

    touser = fields.Many2one('hr.employee', string="接收者")
    template_id = fields.Char(string="模板")
    url = fields.Char(string="跳转地址")
    msg = fields.Char(string="消息")
    oa_order = fields.Many2one('oa', string="oa单据号")
    order = fields.Char(string="业务单据号")
    approval = fields.Char(string="下级审批人")
    date = fields.Char(string="时间")
    msg_state = fields.Char(string="发送状态")

    rescode = {-1: "系统繁忙",
               0: "请求成功",
               40001: "验证失败",
               40002: "不合法的凭证类型",
               40003: "不合法的OpenID",
               40004: "不合法的媒体文件类型",
               40005: "不合法的文件类型",
               40006: "不合法的文件大小",
               40007: "不合法的媒体文件id",
               40008: "不合法的消息类型",
               40009: "不合法的图片文件大小",
               40010: "不合法的语音文件大小",
               40011: "不合法的视频文件大小",
               40012: "不合法的缩略图文件大小",
               40013: "不合法的APPID",
               41001: "缺少access_token参数",
               41002: "缺少appid参数",
               41003: "缺少refresh_token参数",
               41004: "缺少secret参数",
               41005: "缺少多媒体文件数据",
               41006: "access_token超时",
               42001: "需要GET请求",
               43002: "需要POST请求",
               43003: "需要HTTPS请求",
               44001: "多媒体文件为空",
               44002: "POST的数据包为空",
               44003: "图文消息内容为空",
               45001: "多媒体文件大小超过限制",
               45002: "消息内容超过限制",
               45003: "标题字段超过限制",
               45004: "描述字段超过限制",
               45005: "链接字段超过限制",
               45006: "图片链接字段超过限制",
               45007: "语音播放时间超过限制",
               45008: "图文消息超过限制",
               45009: "接口调用超过限制",
               46001: "不存在媒体数据",
               47001: "解析JSON / XML内容错误"}

    @api.model
    def create(self, vals_list):
        order = super(msg_templete, self).create(vals_list)
        order.sned_message()
        return order

    def sned_message(self):
        '''

        :param touser:接收者wx openid
        :param template_id:消息模板
        :param url:消息点击跳转地址
        :param msg:驳回/提交 消息
        :param oa_order:oa单据号
        :param order:业务单据号
        :param approval:下级审批人
        :param date:操作时间
        :return:
        '''
        conn = http.client.HTTPSConnection("api.weixin.qq.com")
        oa_wx_id = self.env['oa.wx'].search([('wx_state', '=', True)])
        payload = json.dumps({
            "touser": self.touser.wx_aaid,
            "template_id": self.template_id,
            "url": self.url,
            "topcolor": "#FF0000",
            "data": {
                "msg": {
                    "value": self.msg,
                    "color": "#d81e06"
                },
                "oa": {
                    "value": self.oa_order.oa_name,
                    "color": "#1296db"
                },
                "order": {
                    "value": self.order,
                    "color": "#1296db"
                },
                "approval": {
                    "value": self.approval,
                    "color": "#00000"
                },
                "date": {
                    "value": self.date,
                    "color": "#2c2c2c"
                }
            }
        })
        headers = {
            'Content-Type': 'application/json'
        }
        conn.request("POST",
                     "/cgi-bin/message/template/send?access_token=%s" % (oa_wx_id.access_token),
                     payload, headers)
        res = conn.getresponse()
        data = res.read()
        result = data.decode("utf-8")
        jsonstr = json.loads(result)
        code = jsonstr['errcode']
        self.msg_state = self.rescode[code]
        print(data.decode("utf-8"))


class wx_inherit_hr_employee(models.Model):
    _inherit = 'hr.employee'
    _description = "微信公众号维护"

    wx_aaid = fields.Char(string="用户的在此公众号的openid")
    qr_image = fields.Binary(string="绑定微信", compute='compute_qr_image')

    def compute_qr_image(self):
        for employee in self:
            # 生成二维码
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            wxinfo = self.env['oa.wx'].search([('wx_state', '=', True)], limit=1)
            if not wxinfo.baseurl:
                raise exceptions.UserError(_("请配置对外域名！"))
            LOGIN_REDIRECT_URL = wxinfo.baseurl + '/flowmanager/call/user?em_id=' + str(self.id)
            self = self.env['oa.wx'].search([('wx_state', '=', True)], limit=1)
            url = '''https://open.weixin.qq.com/connect/oauth2/authorize?appid=%s&redirect_uri=%s&response_type=code&scope=snsapi_base&state=ok#wechat_redirect''' % (
                wxinfo.appid, LOGIN_REDIRECT_URL)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            employee.qr_image = qr_image
