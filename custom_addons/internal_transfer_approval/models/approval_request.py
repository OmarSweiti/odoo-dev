# -*- coding: utf-8 -*-
"""
Internal Transfer Approval Module

This module provides an approval workflow for internal transfers.
Requests must be approved by a manager before stock pickings are created.

Features:
- Creates approval requests for internal transfers
- State machine: Draft -> To Approve -> Approved/Rejected
- Automatic stock.picking generation on approval
- Proper state tracking and audit trail
"""

from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class InternalApprovalRequestLine(models.Model):
    """
    Model for internal transfer approval request line items.
    Contains the products and quantities to be transferred.
    """
    
    _name = "internal.approval.request.line"
    _description = "Internal Transfer Approval Line"
    _order = "sequence, id"
    
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Sequence for ordering the lines"
    )
    request_id = fields.Many2one(
        'internal.approval.request',
        string="Request",
        required=True,
        ondelete='cascade',
        index=True
    )
    product_id = fields.Many2one(
        'product.product',
        string="Product",
        required=True,
        ondelete='restrict',
        domain="[('type', 'in', ['product', 'consu'])]"
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string="Unit of Measure",
        required=True,
        ondelete='restrict'
    )
    quantity = fields.Float(
        string="Quantity",
        required=True,
        default=1.0,
        digits='Product Unit of Measure',
        help="Quantity to transfer"
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string="Product Template",
        related='product_id.product_tmpl_id',
        readonly=True
    )
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set default UoM when product changes."""
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
    
    @api.constrains('quantity')
    def _check_quantity_positive(self):
        """Ensure quantity is positive."""
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero."))


class InternalApprovalRequest(models.Model):
    """
    Model for handling internal transfer approval requests.
    
    This model provides a workflow for requesting and approving internal
    transfers before they are executed in the system.
    """
    
    _name = "internal.approval.request"
    _description = "Internal Transfer Approval"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference'
    _order = 'create_date desc'
    
    # State machine for approval workflow
    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('to_approve', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    reference = fields.Char(
        string="Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    source_location_id = fields.Many2one(
        "stock.location",
        string="Source Location",
        required=True,
        domain="[('usage', '=', 'internal')]",
        tracking=True
    )
    dest_location_id = fields.Many2one(
        "stock.location",
        string="Destination Location",
        required=True,
        domain="[('usage', '=', 'internal')]",
        tracking=True
    )
    state = fields.Selection(
        STATE_SELECTION,
        default='draft',
        readonly=True,
        string="Status",
        tracking=True
    )
    requester_id = fields.Many2one(
        'res.users',
        string="Requested By",
        readonly=True,
        default=lambda self: self.env.user
    )
    approver_id = fields.Many2one(
        'res.users',
        string="Approved By",
        readonly=True,
        copy=False
    )
    approval_date = fields.Datetime(
        string="Approval Date",
        readonly=True,
        copy=False
    )
    rejection_reason = fields.Text(
        string="Rejection Reason",
        readonly=True,
        copy=False
    )
    picking_id = fields.Many2one(
        'stock.picking',
        string="Stock Transfer",
        readonly=True,
        copy=False,
        help="The stock picking created after approval"
    )
    note = fields.Text(
        string="Notes",
        help="Additional notes for the transfer"
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        readonly=True,
        default=lambda self: self.env.company
    )
    line_ids = fields.One2many(
        'internal.approval.request.line',
        'request_id',
        string="Products",
        copy=True,
        help="Products to be transferred"
    )
    request_state = fields.Selection(
        STATE_SELECTION,
        string="Request State",
        related='state',
        readonly=True,
        store=True
    )
    
    @api.model
    def create(self, vals):
        """
        Create a new approval request with a unique reference.
        
        Args:
            vals (dict): Dictionary containing field values
            
        Returns:
            Recordset: The newly created approval request
        """
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code(
                'internal.approval.request'
            ) or _('New')
        return super().create(vals)
    
    def action_submit_for_approval(self):
        """
        Submit the request for approval.
        
        Returns:
            bool: True if successful
            
        Raises:
            UserError: If no products are added or state is not draft
        """
        for request in self:
            if request.state != 'draft':
                raise UserError(_(
                    "Only draft requests can be submitted for approval."
                ))
            if not request.line_ids:
                raise UserError(_(
                    "Please add at least one product to transfer."
                ))
            request.write({
                'state': 'to_approve',
            })
            # Send notification to approvers (managers)
            self._send_approval_notification()
        return True
    
    def action_approve(self):
        """
        Approve the request and create the stock picking.
        
        Returns:
            bool: True if successful
        """
        for request in self:
            if request.state != 'to_approve':
                raise UserError(_(
                    "Only requests waiting for approval can be approved."
                ))
            
            # Create the stock picking with move lines
            picking = request._create_stock_picking()
            
            # Update the request
            request.write({
                'state': 'approved',
                'approver_id': self.env.user.id,
                'approval_date': fields.Datetime.now(),
                'picking_id': picking.id,
            })
            
            # Log the approval in the chatter
            request.message_post(
                body=_("Request approved by %s", self.env.user.name),
                subject=_("Request Approved")
            )
            
            # Create activity for requester
            request.requester_id.notify_info(
                _("Your transfer request %s has been approved.") % request.reference
            )
        return True
    
    def action_reject(self, reason=''):
        """
        Reject the request.
        
        Args:
            reason (str): Reason for rejection
            
        Returns:
            bool: True if successful
        """
        for request in self:
            if request.state != 'to_approve':
                raise UserError(_(
                    "Only requests waiting for approval can be rejected."
                ))
            
            request.write({
                'state': 'rejected',
                'approver_id': self.env.user.id,
                'approval_date': fields.Datetime.now(),
                'rejection_reason': reason,
            })
            
            # Log the rejection in the chatter
            request.message_post(
                body=_("Request rejected by %s. Reason: %s", 
                      self.env.user.name, reason or _('No reason provided')),
                subject=_("Request Rejected")
            )
            
            # Create activity for requester
            request.requester_id.notify_warning(
                _("Your transfer request %s has been rejected.") % request.reference
            )
        return True
    
    def action_reset_to_draft(self):
        """
        Reset the request back to draft state.
        
        Returns:
            bool: True if successful
        """
        for request in self:
            if request.state == 'approved':
                raise UserError(_(
                    "Approved requests cannot be reset to draft."
                ))
            request.write({
                'state': 'draft',
                'approver_id': False,
                'approval_date': False,
                'rejection_reason': False,
            })
        return True
    
    def _create_stock_picking(self):
        """
        Create the stock picking for the approved transfer.
        
        Creates the picking along with stock moves and move lines
        based on the approval request lines.
        
        Returns:
            Recordset: The created stock.picking record
        """
        self.ensure_one()
        
        # Get internal picking type
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        
        if not picking_type:
            raise UserError(_(
                "No internal picking type found for company %s. "
                "Please configure stock operations.",
                self.company_id.name
            ))
        
        # Create the picking
        picking_vals = {
            'picking_type_id': picking_type.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': self.dest_location_id.id,
            'origin': self.reference,
            'note': self.note or '',
            'company_id': self.company_id.id,
        }
        
        picking = self.env['stock.picking'].create(picking_vals)
        
        # Create stock moves for each line
        for line in self.line_ids:
            move_vals = {
                'name': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_uom_id.id,
                'location_id': self.source_location_id.id,
                'location_dest_id': self.dest_location_id.id,
                'picking_id': picking.id,
                'company_id': self.company_id.id,
            }
            move = self.env['stock.move'].create(move_vals)
            
            # Create stock move line for immediate transfer
            self.env['stock.move.line'].create({
                'move_id': move.id,
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom_id.id,
                'location_id': self.source_location_id.id,
                'location_dest_id': self.dest_location_id.id,
                'picking_id': picking.id,
                'qty_done': line.quantity,
                'company_id': self.company_id.id,
            })
        
        # Log the creation
        _logger.info(
            "Stock picking %s created from approval request %s with %d moves",
            picking.name, self.reference, len(self.line_ids)
        )
        
        return picking
    
    def _send_approval_notification(self):
        """
        Send notification to managers about pending approval requests.
        """
        # Find users with approver rights (managers/admins)
        manager_group = self.env.ref('base.group_system')
        if not manager_group:
            return
        
        manager_users = manager_group.users
        for user in manager_users:
            # Create activity for each manager
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary=_("Transfer Approval Required"),
                note=_(
                    "New transfer request %s requires your approval.\n"
                    "From: %s\nTo: %s\nProducts: %d items",
                    self.reference,
                    self.source_location_id.display_name,
                    self.dest_location_id.display_name,
                    len(self.line_ids)
                ),
            )
    
    @api.constrains('source_location_id', 'dest_location_id')
    def _check_locations_different(self):
        """
        Ensure source and destination are different.
        """
        for request in self:
            if request.source_location_id == request.dest_location_id:
                raise ValidationError(_(
                    "Source and destination locations must be different."
                ))
    
    def name_get(self):
        """
        Custom name display for the request.
        
        Returns:
            list: List of (id, display_name) tuples
        """
        result = []
        for request in self:
            display_name = f"{request.reference} ({dict(request.STATE_SELECTION).get(request.state, request.state)})"
            result.append((request.id, display_name))
        return result
    
    def action_view_picking(self):
        """
        Open the associated stock picking.
        
        Returns:
            dict: Window action to open the picking
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.picking_id.id,
            'target': 'current',
        }
    
    def action_add_products(self):
        """
        Open a wizard to add products to the transfer.
        
        Returns:
            dict: Window action to open product selection wizard
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'internal.approval.request.line',
            'view_mode': 'tree,form',
            'domain': [('request_id', '=', self.id)],
            'target': 'current',
        }

