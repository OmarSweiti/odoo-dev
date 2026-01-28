# Odoo Modules Testing and Fixing Plan

## Issues Found and Fixes

### 1. Missing data file in manifest ✅ FIXED
- **Issue**: `data/stock_location.xml` is not included in `hospitality_pos_expense/__manifest__.py`
- **Fix**: Added `data/stock_location.xml` to the manifest

### 2. Duplicate sequence definition ✅ FIXED
- **Issue**: The `internal.approval.request` sequence is defined in BOTH modules
  - `hospitality_pos_expense/data/ir_sequence.xml`
  - `internal_transfer_approval/data/ir_sequence.xml`
- **Fix**: Removed the duplicate sequence from hospitality_pos_expense

### 3. Odoo configuration for websocket/longpolling ✅ FIXED
- **Issue**: Websocket error due to workers configuration
- **Fix**: Updated odoo.conf for proper longpolling (added longpolling_port and gevent_port)

### 4. Test scripts created ✅ DONE
- **test_modules.py**: Python test script for module validation
- **verify_modules.py**: XML-RPC verification script
- **README_TESTING.md**: Comprehensive testing guide

## Tasks

- [x] 1. Fix hospitality_pos_expense manifest (add stock_location.xml)
- [x] 2. Remove duplicate sequence from hospitality_pos_expense
- [x] 3. Update odoo.conf for proper longpolling
- [x] 4. Create module test script
- [ ] 5. Restart Odoo and verify modules load correctly
- [ ] 6. Test hospitality_pos_expense module functionality
- [ ] 7. Test internal_transfer_approval module functionality

## Module Descriptions

### hospitality_pos_expense
- **Purpose**: Enable POS users to record hospitality expenses (free meals for employees)
- **Features**: Creates internal transfers to Inventory Loss location, no sales invoice
- **Depends on**: point_of_sale, stock

### internal_transfer_approval
- **Purpose**: Approval workflow for internal transfers
- **Features**: Draft -> To Approve -> Approved/Rejected state machine
- **Depends on**: stock

## Test Checklist

### Unit Tests
- [ ] Sequence creation
- [ ] Model creation
- [ ] Access rights
- [ ] View rendering

### Integration Tests
- [ ] Module installation
- [ ] Menu access
- [ ] Button visibility (POS)
- [ ] RPC calls

### Functional Tests
- [ ] Create hospitality expense from POS
- [ ] Create approval request
- [ ] Approve/reject workflow
- [ ] Stock picking creation

