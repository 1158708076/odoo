# -*- coding: utf-8 -*-
{
    'license': 'LGPL-3',
    'name': "流程管理",
    'summary': """
       暂时没有描述""",
    'description': """
    流程管理，实现基础表单和流程分离
    支持对接微信公众号
    支持微信接收审批消息和手机端查看单据
    搭载最新工作流引擎实现审批流和工作流的混合运行，实现流程的精准业务化
    """,
    'price': 707,
    'currency': 'EUR',
    'author': "一叶障目",
    'website': "http://www.yourcompany.com",
    'category': 'OA',
    'version': '14.0.1',
    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'hr', 'auth_signup', 'web'],

    # always loaded
    'data': [
        'security/flowmanager_security.xml',
        'security/ir.model.access.csv',
        'models/wizard/oaflow_context_view.xml',
        'views/oa_views.xml',
        'views/oa_flow_views.xml',
        'views/oa_ordertype.xml',
        'views/oa_entrust_view.xml',
        'views/oa_wx.xml',
        'views/templates.xml',
        'views/auth_wx_login.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': [
        'static/src/xml/tree_form_view_button.xml'
    ],
    'application': True,
    'sequence': 1,
    'bootstrap': True,
}
