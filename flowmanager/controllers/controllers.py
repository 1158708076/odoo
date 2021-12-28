# -*- coding: utf-8 -*-
import http.client as httpclient
import json

from odoo import http
from odoo.http import request


class Flowmanager(http.Controller):

    @http.route(['/flowmanager/call'], type='http', auth='public', website=True)
    def wx_call(self):
        return http.request.render('flowmanager.call_page')

    @http.route(['/flowmanager/call/user'], type='http', auth='public')
    def wx_call_user(self, **kw):
        print(kw)
        eminfo = http.request.env['hr.employee'].sudo().search([('id', '=', kw['em_id'])], limit=1)
        jsoninfo = json.loads(self.getopenid(kw['code']))
        openid = jsoninfo['openid']
        eminfo.write({
            'wx_aaid': openid
        })
        return '''<p style="font-size:100px;width: 100%; height: 100%; text-align: center; display: flex; flex-flow: column; justify-content: center;color: green;">授权成功！</p>'''

    def getopenid(self, js_code):
        conn = httpclient.HTTPSConnection("api.weixin.qq.com")
        wxinfo = http.request.env['oa.wx'].sudo().search([('wx_state', '=', True)], limit=1)
        payload = ''
        headers = {}
        url = "/sns/oauth2/access_token?appid=%s&secret=%s&code=%s&grant_type=authorization_code" % (
            wxinfo.appid, wxinfo.secret, js_code)
        conn.request("GET", url, payload, headers)
        res = conn.getresponse()
        data = res.read()
        print(data.decode("utf-8"))
        return data.decode("utf-8")

    @http.route('/wx/login', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        # qcontext = self.get_auth_signup_qcontext()
        # if not qcontext.get('token') and not qcontext.get('wx_login'):
        #     raise werkzeug.exceptions.NotFound()
        #
        # if 'error' not in qcontext and request.httprequest.method == 'POST':
        #     try:
        #         pass
        #     except UserError as e:
        #         qcontext['error'] = e.args[0]
        #     except Exception as e:
        #         qcontext['error'] = str(e)
        response = request.render('flowmanager.wxlogin')
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route(['/flowmanager/call/user/login'], type='http', auth='public')
    def wx_call_user_login(self, **kw):
        print(kw)
        jsoninfo = json.loads(self.getopenid(kw['code']))
        openid = jsoninfo['openid']
        eminfo = http.request.env['hr.employee'].sudo().search([('wx_aaid', '=', openid)], limit=1)
        if not eminfo.user_id:
            return '''<p style="font-size:100px;width: 100%; height: 100%; text-align: center; display: flex; flex-flow: column; justify-content: center;color: red;">您不是此系统用户，无法登录，请联系管理员！</p>'''
        # 验证核心函数，返回数据库中用户id
        # uid = request.session.authenticate(request.session.db, eminfo.user_id.login,
        #                                    '$pbkdf2-sha512$25000$HYOwFsL4H8MYI2TM2XsvJQ$x5eThU8TDZZ7IPuVDXq4tSly6iNZ.tiMd9jsZo743B2kiA1UE0Erb3Vd9wkT8f71LwFlPJLmcfy.x08S/iz4Gg')
        # if uid is False:
        #     return '''<p style="font-size:100px;width: 100%; height: 100%; text-align: center; display: flex; flex-flow: column; justify-content: center;color: red;">验证失败！</p>'''

        # 验证核心函数，返回数据库中用户id
        uid = request.session.authenticate(request.session.db, eminfo.user_id.login, openid)
        # if uid is False:
        #     # 以超级管理员创建用户
        #     request.env['res.users'].sudo().create({
        #         "login": user_info['nickname'],  # 登入名，可重复
        #         "password": user_info['openid'],  # 我这里把openID当做密码
        #         "name": user_info['nickname'],  # 用户名，不可重复
        #         "oauth_provider_id": provider_id,  # 服务商id，可选
        #         "city": city,  # 可选，还可添加其他参数，这里就不列举了
        #         # 将该用户添加到门户组, 如果是员工登入就不设置"groups_id"
        #         "groups_id": request.env.ref('base.group_portal'),
        #     })
        #     # 待解决：因为新用户第一次验证不成功，第二次再扫的时候就可以，
        #     # 所以我这里跳转到重新登入，希望大神解决这个问题
        #     return http.local_redirect('/web/login')
        return http.local_redirect('/')


# class google(Home):
#
#     @http.route('/web/login', type='http', auth='public', website=True)
#     def web_login(self, *args, **kargs):
#         if request.httprequest.method == 'POST' and not request.params.get('qsso'):
#             # Check Google Authentication
#             uids = request.registry.get('res.users').search(request.cr, odoo.SUPERUSER_ID,
#                                                             [('login', '=', request.params['login'])])
#             qcontext = {}
#             if not len(uids):
#                 qcontext['error'] = _("User doesn't exist! Please contact system administrator!")
#             user = request.registry.get('res.users').browse(request.cr, odoo.SUPERUSER_ID, uids)
#
#             if user.enable_google_auth and user.otp_str:
#                 totp = pyotp.TOTP(user.otp_str)
#                 otpcode = totp.now()
#                 check_code = request.params['password'][-6:]
#                 check_passwd = request.params['password'][:-6]
#                 if request.params['password'][-6:] == otpcode:
#                     request.params['password'] = check_passwd
#                     return super(google, self).web_login(*args, **kargs)
#                 else:
#                     qcontext['error'] = 'Your Google Authentication Failed!'
#                     return request.render('web.login', qcontext)
#         return super(google, self).web_login(*args, **kargs)
