# TODO: Fix ParseError - Invalid composed field request_id.state in attrs

## Task Summary
Fix Odoo ParseError by replacing dot-notation in attrs with a related field.

## Steps Completed
- [x] 1. Add `request_state` related field to `InternalApprovalRequest` model (main form model)
- [x] 2. Add `<field name="request_state" invisible="1"/>` in XML view header
- [x] 3. Replace `request_id.state` with `request_state` in attrs for line_ids tree view

## Fix Applied
The `request_state` field was added to the main model (`InternalApprovalRequest`) not the Line model, since the form view's header belongs to the main model.

