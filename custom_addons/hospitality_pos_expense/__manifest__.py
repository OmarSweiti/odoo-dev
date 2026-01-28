# -*- coding: utf-8 -*-
{
    'name': "POS Hospitality Expense",
    'version': '1.0',
    'category': 'Point of Sale',
    'description': """
POS Hospitality Expense Module
==============================

This module enables POS users to record hospitality expenses (free meals for employees)
as internal transfers from the main warehouse to an "Inventory Loss" location,
without generating sales invoices.

Features:
- Creates internal transfers for hospitality expenses
- Records employee names with each transfer
- Controlled by access rights (group-based)
- No sales invoice generated
    """,
    'depends': [
        'base',
        'point_of_sale',
        'stock',
        'mail',
        'web',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/stock_location.xml',
        'views/pos_hospitality_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'hospitality_pos_expense/static/src/js/hospitality_button.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

