# -*- coding: utf-8 -*-
{
    'name': "stock_oil_management",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale_management', 'stock', 'hr', 'contacts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/stock_move_decimal_precision.xml',
        'views/product_product_inherit_views.xml',
        'views/stock_picking_inherit_views.xml',
        'views/transport_views.xml',
        'views/sale_order_inherit.xml',
        'views/ilot_views.xml',
        'views/regime_douanier.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
