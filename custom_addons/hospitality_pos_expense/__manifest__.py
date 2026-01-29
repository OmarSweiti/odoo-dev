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
- Automatic accounting entries in Hospitality Expense account

Case 1: POS Button for Hospitality Expense
-------------------------------------------
Enable selected POS users (e.g., restaurant cashiers) to deduct a free meal per 
employee by recording it as a hospitality expense instead of a sale.

The process:
1. User selects products in POS
2. Clicks "Hospitality Expense" button
3. Prompts for employee name
4. Creates internal transfer from warehouse to Inventory Loss
5. Generates accounting journal entries
6. No invoice or sales record is generated
    """,
    'depends': [
        'base',
        'point_of_sale',
        'stock',
        'mail',
        'web',
        'account',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/stock_location.xml',
        'data/account_data.xml',
        'views/pos_hospitality_views.xml',
    ],
    'assets': {
        # Frontend JavaScript for POS interface
        'web.assets_frontend': [
            'hospitality_pos_expense/static/src/js/hospitality_button.js',
        ],
        # QWeb templates for POS button
        'web.assets_qweb': [
            'hospitality_pos_expense/static/src/xml/pos_hospitality_templates.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

