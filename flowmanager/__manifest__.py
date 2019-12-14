# -*- coding: utf-8 -*-
{
    'license': 'LGPL-3',
    'name': "流程管理",
    'summary': """
       暂时没有描述""",
    'description': """
    流程管理，实现基础表单和流程分离
    """,
    'price': 110,
    'currency': 'EUR',
    'author': "一叶障目",
    'website': "http://www.yourcompany.com",
    'category': 'OA',
    'version': '11.0.1',
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
        'views/oa_entrust_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'sequence': 1,
}
