# -*- coding: utf-8 -*-
{
    'name': "流程管理",

    'summary': """
       暂时没有描述""",

    'description': """
    流程管理，实现基础表单和流程分离
    """,

    'author': "一叶障目",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'OA',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'hr'],

    # always loaded
    'data': [
        'security/flowmanager_security.xml',
        'security/ir.model.access.csv',
        'models/wizard/oaflow_context_view.xml',
        'views/oa_views.xml',
        'views/oa_flow_views.xml',
        'views/oa_ordertype.xml',
        # 'views/oa_sale_order_views.xml',
        # 'views/oa_purchase_order_views.xml',
        # 'views/templates.xml',
        'views/oa_entrust_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'sequence': 1,
    # 'qweb': [
    #     'static/src/xml/oa_flow_activity.xml',
    # ],
}
