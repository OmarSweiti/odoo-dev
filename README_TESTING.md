# Odoo Custom Modules - Testing Guide

## Overview

This directory contains two custom Odoo modules:
1. **hospitality_pos_expense** - POS Hospitality Expense Management
2. **internal_transfer_approval** - Internal Transfer Approval Workflow

## Quick Start

### 1. Fix Applied

The following fixes have been applied:
- ✅ Added `data/stock_location.xml` to `hospitality_pos_expense` manifest
- ✅ Removed duplicate sequence from `hospitality_pos_expense`
- ✅ Updated `odoo.conf` for proper longpolling

### 2. Restart Odoo Server

```bash
# Stop existing Odoo (Ctrl+C if running)
# Then restart:
cd /home/omars_odoo_dev/od voo-dev
sourceenv/bin/activate
./odoo/odoo-bin -c odoo.conf
```

### 3. Upgrade Modules

In Odoo UI:
1. Go to Apps
2. Search for "Hospitality" → Click Upgrade
3. Search for "Transfer Approval" → Click Upgrade
4. Click Update Apps List if modules not visible

Or via command line:
```bash
python -c "
import odoo
from odoo import api, SUPERUSER_ID

registry = odoo.modules.registry.Registry('my-odoo-db')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    modules = env['ir.module.module']
    
    for name in ['hospitality_pos_expense', 'internal_transfer_approval']:
        module = modules.search([('name', '=', name)])
        if module:
            module.button_immediate_upgrade()
            print(f'Upgraded: {name}')
"
```

## Module Verification

### Option 1: Via Python Script (Recommended)

```bash
cd /home/omars_odoo_dev/odoo-dev
source venv/bin/activate

# Test while Odoo is running
python verify_modules.py -d my-odoo-db -w admin
```

Expected output:
```
✓ Authenticated successfully (UID: X)
Testing module: hospitality_pos_expense
  - Module state: installed
  ✓ hospitality_pos_expense is installed
...
✓ All modules are properly installed!
```

### Option 2: Via Odoo Shell

```bash
cd /home/omars_odoo_dev/odoo-dev
source venv/bin/activate
./odoo/odoo-bin shell -d my-odoo-db --no-http
```

Then in shell:
```python
# Check modules
modules = env['ir.module.module'].search([('name', 'in', ['hospitality_pos_expense', 'internal_transfer_approval'])])
for m in modules:
    print(f"{m.name}: {m.state}")

# Check models
for model in ['pos.hospitality.expense', 'pos.hospitality.expense.line', 'internal.approval.request']:
    try:
        fields = env[model].fields_get()
        print(f"{model}: {len(fields)} fields")
    except Exception as e:
        print(f"{model}: ERROR - {e}")
```

### Option 3: Manual Verification via Browser

1. **Hospitality POS Expense**:
   - Go to Point of Sale → Hospitality Expenses
   - Should see "Hospitality Expenses" menu
   - Create new expense with employee name

2. **Internal Transfer Approval**:
   - Go to Inventory → Transfer Approvals
   - Should see "Transfer Approvals" menu
   - Create new approval request

## Testing Checklist

### Unit Tests

- [ ] Module appears in Apps list
- [ ] Module can be installed/updated
- [ ] Security groups created
- [ ] Sequences created with correct prefixes
- [ ] Access rights configured

### Integration Tests

- [ ] Model can be created/read
- [ ] Views render correctly
- [ ] Actions work
- [ ] Menus visible to authorized users
- [ ] RPC calls work

### Functional Tests

#### Hospitality POS Expense

1. Open POS interface
2. Add products to order
3. Click "Hospitality Expense" button
4. Enter employee name
5. Confirm the transfer
6. Verify stock picking created
7. Check inventory loss location

#### Internal Transfer Approval

1. Go to Inventory → Transfer Approvals
2. Create new request
3. Submit for approval
4. Login as manager
5. Approve the request
6. Verify stock picking created
7. Check transfer completed

## Common Issues

### Websocket Error
```
RuntimeError: Couldn't bind the websocket. Is the connection opened on the evented port (8072)?
```

**Solution**: The `odoo.conf` has been updated. Ensure you're using:
```ini
longpolling_port = 8072
gevent_port = 8072
```

### Module Not Found
If modules don't appear in Apps:
1. Click "Update Apps List" button
2. Refresh browser
3. Check logs for loading errors

### Access Rights Issues
If users can't see menus:
1. Go to Settings → Users & Companies → Users
2. Edit user
3. Add to "Hospitality POS Access" or "Transfer Approval" group

### Sequence Not Found
If sequences don't exist after install:
1. Upgrade the module
2. Check `ir_sequence` table for entries
3. Verify `ir_sequence_code` table

## File Structure

```
/home/omars_odoo_dev/odoo-dev/
├── custom_addons/
│   ├── hospitality_pos_expense/
│   │   ├── __manifest__.py
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── pos_hospitality.py
│   │   ├── views/
│   │   │   ├── pos_hospitality_views.xml
│   │   │   └── assets.xml
│   │   ├── security/
│   │   │   ├── security.xml
│   │   │   └── ir.model.access.csv
│   │   ├── data/
│   │   │   ├── ir_sequence.xml
│   │   │   └── stock_location.xml
│   │   └── static/
│   │       └── src/
│   │           └── js/
│   │               └── hospitality_button.js
│   │
│   └── internal_transfer_approval/
│       ├── __manifest__.py
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   └── approval_request.py
│       ├── views/
│       │   └── approval_view.xml
│       ├── security/
│       │   ├── security.xml
│       │   └── ir.model.access.csv
│       └── data/
│           └── ir_sequence.xml
│
├── odoo.conf
├── test_modules.py        # Python test script
├── verify_modules.py      # XML-RPC verification script
└── README.md              # This file
```

## Support

If issues persist:
1. Check Odoo logs for errors
2. Verify all dependencies are installed
3. Check database for module records
4. Ensure proper access rights

## Next Steps

After verification:
1. Assign groups to users
2. Configure inventory locations
3. Test with real products
4. Train users on workflow
5. Monitor usage and logs

