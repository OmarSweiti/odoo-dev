# Odoo Custom Modules - Complete Testing Guide

## Overview

This guide provides detailed instructions to test and use your two custom Odoo modules:

1. **hospitality_pos_expense** - POS Hospitality Expense Management
2. **internal_transfer_approval** - Internal Transfer Approval Workflow

---

## Prerequisites

### 1. Start Odoo Server

```bash
cd /home/omars_odoo_dev/odoo-dev
source venv/bin/activate
./odoo/odoo-bin -c odoo.conf
```

Odoo will start on:
- Web interface: http://localhost:8069
- XML-RPC: http://localhost:8069/xmlrpc/2
- Longpolling: http://localhost:8072

### 2. Access Odoo Web Interface

1. Open your browser and go to: **http://localhost:8069**
2. Login with your admin credentials (default: admin/admin)
3. You should see the Odoo dashboard

---

## Module Installation Verification

### Option A: Using the Verification Script (Recommended)

While Odoo is running, open a new terminal:

```bash
cd /home/omars_odoo_dev/odoo-dev
source venv/bin/activate

python verify_modules.py -d your_database_name -w admin
```

Replace `your_database_name` with your actual database name.

**Expected output:**
```
✓ Authenticated successfully (UID: X)
Testing module: hospitality_pos_expense
  - Module state: installed
  ✓ hospitality_pos_expense is installed
  ✓ Model accessible with XX fields
  ✓ Sequence found: HPE/...
...
✓ All modules are properly installed!
```

### Option B: Manual Verification in Odoo

1. Go to **Apps** (top menu)
2. Click **Update Apps List** button (top right)
3. Search for "Hospitality" - you should see "POS Hospitality Expense"
4. Search for "Transfer" - you should see "Internal Transfer Approval"
5. If they show "Install" instead of "Upgrade", click to install them

---

## Testing Module 1: hospitality_pos_expense

### Step 1: Access the Module

1. In Odoo, go to: **Point of Sale** → **Hospitality Expenses**
2. You should see a list view with columns: Reference, Employee Name, Status, Created
3. If you don't see the menu, check your user permissions (see Section 6)

### Step 2: Create a Hospitality Expense

1. Click **Create** button
2. Fill in the fields:
   - **Employee Name**: Enter the employee's name (required)
   - **Notes**: Optional notes about the expense
3. Click **Save**
4. Note the **Reference** number (e.g., HPE/00001)

### Step 3: Use the POS Interface

1. Open a new browser tab and go to **Point of Sale** → **Point of Sale**
2. Select a POS session
3. Add products to the order
4. Look for the **"Hospitality Expense"** button (in the footer or action buttons)
5. Click it and enter:
   - **Employee Name**: Name of the employee
6. Confirm the transfer
7. A stock picking will be created automatically

### Step 4: Verify Stock Transfer

1. Go to **Inventory** → **Operations** → **Transfers**
2. Search for transfers with origin "Hospitality Expense"
3. You should see:
   - Transfer from your main warehouse to "Inventory Loss (Hospitality)"
   - Status: Done
   - Move lines with the products you selected

### Step 5: Check the Expense Record

1. Go to **Point of Sale** → **Hospitality Expenses**
2. Find your expense record
3. Click to open it
4. You should see:
   - State: Completed
   - Linked Stock Transfer (clickable link)
   - Employee name and notes

---

## Testing Module 2: internal_transfer_approval

### Step 1: Access the Module

1. In Odoo, go to: **Inventory** → **Transfer Approvals**
2. You should see a list view with columns: Reference, Source, Destination, Status, Requester
3. If you don't see the menu, check your user permissions (see Section 6)

### Step 2: Create an Approval Request

1. Click **Create** button
2. Fill in the fields:
   - **Source Location**: Select a source warehouse location (required)
   - **Destination Location**: Select a destination location (required)
   - **Notes**: Optional notes about the transfer
3. Add products to transfer:
   - Click **Add a line** in the Products section
   - Select a **Product** (must be storable or consumable)
   - Enter **Quantity**
   - Unit of Measure auto-fills
4. Click **Save**
5. Note the **Reference** number (e.g., IAR/00001)

### Step 3: Submit for Approval

1. With the request open, click the **Submit for Approval** button
2. Status changes from "Draft" to "Waiting for Approval"
3. The requester can no longer edit it
4. Notifications are sent to managers

### Step 4: Approve the Request (as Manager)

1. Login as a user with manager privileges (e.g., admin)
2. Go to **Inventory** → **Transfer Approvals**
3. Find the request with status "Waiting for Approval"
4. Open it and review the details
5. Click **Approve** button
6. The following happens automatically:
   - Status changes to "Approved"
   - A Stock Picking is created
   - The Approver and Approval Date are recorded
7. Click the **Stock Transfer** link to view the picking

### Step 5: Reject the Request (Optional)

1. Open a request with status "Waiting for Approval"
2. Click **Reject** button
3. Enter a rejection reason (optional)
4. Status changes to "Rejected"
5. The requester is notified

### Step 6: Reset to Draft (Optional)

1. Open a rejected or pending request
2. Click **Reset to Draft** button
3. Status changes back to "Draft"
4. You can now edit and resubmit

### Step 7: Verify the Stock Picking

1. Go to **Inventory** → **Operations** → **Transfers**
2. Find the transfer with origin matching your request reference
3. Open it to see:
   - Source and destination locations
   - Move lines with products
   - Quantities transferred

---

## User Permissions Setup

### Assign Groups to Users

By default, users need proper group assignments to access the modules.

### For hospitality_pos_expense:

1. Go to **Settings** → **Users & Companies** → **Users**
2. Edit the user who needs access
3. In the **Access Rights** tab, scroll to **Hospitality POS Expense**
4. Check **Hospitality POS Access** (if visible)
5. Or add the user to the "Hospitality POS Expense / User" group

### For internal_transfer_approval:

1. Go to **Settings** → **Users & Companies** → **Users**
2. Edit the user who needs access
3. In the **Access Rights** tab, scroll to **Internal Transfer Approval**
4. Check **Transfer Approval Access** (if visible)
5. Or add the user to the "Internal Transfer Approval / User" group

### For Managers (Approval Rights):

1. Users need to be in the "Administration / Settings" group (base.group_system) to approve requests
2. Or create a custom approval group in **Settings** → **Users & Companies** → **Groups**

---

## Testing Checklist

### Hospitality POS Expense Module

| Test | Expected Result |
|------|-----------------|
| Menu visible in POS | Point of Sale → Hospitality Expenses |
| Can create expense | New record created with reference |
| Employee name required | Error if empty |
| POS button visible | "Hospitality Expense" button in POS |
| Transfer created | Stock picking in Inventory |
| Location correct | Products moved to Inventory Loss |
| Status updates | Draft → Completed |

### Internal Transfer Approval Module

| Test | Expected Result |
|------|-----------------|
| Menu visible in Inventory | Inventory → Transfer Approvals |
| Can create request | New record with reference |
| Source ≠ Destination | Error if same location |
| Products required | Error if no lines |
| Submit for approval | Status → Waiting for Approval |
| Approve request | Status → Approved, Picking created |
| Reject request | Status → Rejected, reason recorded |
| View picking | Linked stock transfer opens |
| Reset to draft | Status → Draft (if not approved) |

---

## Common Issues and Solutions

### Issue 1: Menu Not Visible

**Cause**: User doesn't have proper access rights

**Solution**:
1. Go to **Settings** → **Users & Companies** → **Users**
2. Edit the user
3. Click **Preferences** tab
4. Add the user to appropriate groups:
   - For Hospitality: "Hospitality POS Expense / User"
   - For Approval: "Internal Transfer Approval / User"
5. Refresh the page

### Issue 2: No Internal Picking Type

**Error**: "No internal picking type found"

**Solution**:
1. Go to **Inventory** → **Configuration** → **Operations Types**
2. Ensure there's at least one picking type with:
   - Type: Internal Transfer
   - Company: Your company
3. If none exists, create one

### Issue 3: No Warehouse Found

**Error**: "No warehouse found"

**Solution**:
1. Go to **Inventory** → **Configuration** → **Warehouses**
2. Create a warehouse for your company
3. Ensure it has a lot_stock_id location

### Issue 4: Inventory Loss Location Not Found

**Error**: "No suitable location found"

**Solution**:
1. Go to **Inventory** → **Configuration** → **Locations**
2. Create a location with:
   - Name: Inventory Loss (Hospitality)
   - Usage: Inventory Loss
   - Company: Your company
3. Or create under Virtual Locations/Parent Locations

### Issue 5: Module Not Appearing in Apps

**Solution**:
1. Go to **Apps**
2. Click **Update Apps List** (top right, three dots menu or button)
3. Wait for update to complete
4. Search for module name
5. If still not found, check:
   - Module is in `custom_addons/` folder
   - `__manifest__.py` is correctly formatted
   - No syntax errors in Python files

---

## Using the Test Scripts

### Run Verification Script

```bash
cd /home/omars_odoo_dev/odoo-dev
source venv/bin/activate
python verify_modules.py -d my_odoo_db -w admin
```

Parameters:
- `-d`: Database name (required)
- `-w`: Admin password (default: admin)
- `-H`: Host (default: localhost)
- `-p`: Port (default: 8069)

### Check Module Status via Shell

```bash
cd /home/omars_odoo_dev/odoo-dev
source venv/bin/activate
./odoo/odoo-bin shell -d my_odoo_db --no-http
```

In the Odoo Shell:

```python
# Check module states
modules = env['ir.module.module'].search([
    ('name', 'in', ['hospitality_pos_expense', 'internal_transfer_approval'])
])
for m in modules:
    print(f"{m.name}: {m.state}")

# Check model fields
for model in ['pos.hospitality.expense', 'internal.approval.request']:
    try:
        fields = env[model].fields_get()
        print(f"{model}: {len(fields)} fields")
    except Exception as e:
        print(f"{model}: ERROR - {e}")

# Check access rights
print("\nAccess Rights:")
for model in ['pos.hospitality.expense', 'internal.approval.request']:
    acl = env['ir.model.access'].check(model, 'read')
    print(f"{model} read: {acl}")
```

---

## Quick Test Commands

### Test 1: Verify Modules Are Installed

```bash
cd /home/omars_odoo_dev/odoo-dev
source venv/bin/activate
python verify_modules.py -d your_db -w admin
```

### Test 2: Create Test Data via Shell

```python
# In Odoo Shell
from odoo import api, SUPERUSER_ID

env = api.Environment(env.cr, SUPERUSER_ID, {})

# Create a hospitality expense
expense = env['pos.hospitality.expense'].create({
    'employee_name': 'Test Employee',
    'note': 'Test expense',
})
print(f"Created expense: {expense.reference}")

# Create an approval request
request = env['internal.approval.request'].create({
    'source_location_id': env['stock.warehouse'].search([], limit=1).lot_stock_id.id,
    'dest_location_id': env['stock.location'].search([('usage', '=', 'inventory')], limit=1).id,
    'note': 'Test transfer',
})
print(f"Created request: {request.reference}")
```

### Test 3: View All Records

```python
# In Odoo Shell
env = api.Environment(env.cr, SUPERUSER_ID, {})

print("\n=== Hospitality Expenses ===")
expenses = env['pos.hospitality.expense'].search([])
for e in expenses:
    print(f"  {e.reference}: {e.employee_name} ({e.state})")

print("\n=== Approval Requests ===")
requests = env['internal.approval.request'].search([])
for r in requests:
    print(f"  {r.reference}: {r.state} ({r.requester_id.name})")
```

---

## Summary

To test your modules:

1. **Start Odoo**: `./odoo/odoo-bin -c odoo.conf`
2. **Access Web UI**: http://localhost:8069
3. **Verify Installation**: Run `python verify_modules.py -d your_db -w admin`
4. **Test hospitality_pos_expense**:
   - Go to Point of Sale → Hospitality Expenses
   - Create expense records
   - Use POS interface with button
5. **Test internal_transfer_approval**:
   - Go to Inventory → Transfer Approvals
   - Create and submit requests
   - Approve as manager
6. **Check Results**: View stock transfers in Inventory → Transfers

If you encounter any issues, refer to the Common Issues section above or check the Odoo server logs.

