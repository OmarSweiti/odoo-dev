# -*- coding: utf-8 -*-
{
    'name': "Internal Transfer Approval",
    'version': '1.0',
    'category': 'Inventory',
    'description': """
Internal Transfer Approval Module
=================================

This module provides an approval workflow for internal transfers.
Requests must be approved by a manager before stock pickings are created.

Features:
- Creates approval requests for internal transfers
- State machine: Draft -> To Approve -> Approved/Rejected
- Automatic stock.picking generation on approval
- Proper state tracking and audit trail
- Menu-based access in Inventory app
    """,
    'depends': [
        'stock',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/approval_view.xml',
        'data/ir_sequence.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

