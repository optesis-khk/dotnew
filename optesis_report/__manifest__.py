{
    'name': 'Vivo Report',

    'description': """
                
            """,

    'author': 'OPTESIS SA BY ANG',
    'website': "http://www.Optesis.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'version': '12.0.0.0.0',
    'category': 'Accounting',

    # any module necessary for this one to work correctly
    'depends': ['stock',],

    'data': [
        'views/report_vivo_plan_c.xml',
        'views/optesis_header_footer.xml',
        'views/optesis_external_layout.xml',
        'views/report_vivo_reception.xml',
        'views/report_vivo_dot.xml',
        'report/optesis_custom_format.xml',
        'report/optesis_custom_format_paysage.xml',
        'report/report.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
    ],

}