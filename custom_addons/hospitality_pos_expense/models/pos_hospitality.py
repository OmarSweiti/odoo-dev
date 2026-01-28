# -*- coding: utf-8 -*-
"""
POS Hospitality Expense Module

This module enables POS users to record hospitality expenses (free meals for employees)
as internal transfers from the main warehouse to an "Inventory Loss" location,
without generating sales invoices.

Features:
- Creates internal transfers for hospitality expenses
- Records employee names with each transfer
- Controlled by access rights (group-based)
- No sales invoice generated
"""

from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError


class PosHospitalityExpense(models.Model):
    """
    Model for handling hospitality expense transfers.
    
    This model provides methods to create internal stock transfers
    that represent hospitality expenses (employee meals) instead of sales.
    """
    
    _name = "pos.hospitality.expense"
    _description = "POS Hospitality Expense"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference'
    _order = 'create_date desc'
    
    reference = fields.Char(
        string="Reference", 
        required=True, 
        copy=False, 
        readonly=True,
        default=lambda self: _('New')
    )
    employee_name = fields.Char(
        string="Employee Name", 
        required=True,
        help="Name of the employee receiving the hospitality expense"
    )
    picking_id = fields.Many2one(
        'stock.picking',
        string="Stock Transfer",
        readonly=True,
        copy=False,
        help="The internal transfer created for this expense"
    )
    line_ids = fields.One2many(
        'pos.hospitality.expense.line',
        'expense_id',
        string="Expense Lines",
        copy=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Completed'),
    ], default='draft', readonly=True, string="Status")
    
    @api.model
    def create(self, vals):
        """
        Create a new hospitality expense record with a unique reference.
        
        Args:
            vals (dict): Dictionary containing field values
            
        Returns:
            Recordset: The newly created hospitality expense record
        """
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code(
                'pos.hospitality.expense'
            ) or _('New')
        return super().create(vals)
    
    def _get_picking_type_internal(self):
        """
        Get the internal picking type for transfers.
        
        Returns:
            Recordset: The stock.picking.type record for internal transfers
        """
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal')
        ], limit=1)
        if not picking_type:
            raise UserError(_("No internal picking type found. "
                            "Please configure stock operations."))
        return picking_type
    
    def _get_source_location(self):
        """
        Get the source location (main warehouse stock).
        
        Returns:
            Recordset: The stock.location for the main warehouse
        """
        warehouse = self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        if not warehouse:
            raise UserError(_("No warehouse found. "
                            "Please configure inventory locations."))
        return warehouse.lot_stock_id
    
    def _get_destination_location(self):
        """
        Get the destination location (Inventory Loss for hospitality).
        
        Returns:
            Recordset: The inventory loss location for hospitality
        """
        location = self.env.ref(
            'hospitality_pos_expense.location_inventory_loss_hospitality',
            raise_if_not_found=False
        )
        if not location:
            # Fallback: search for inventory loss type location
            location = self.env['stock.location'].search([
                ('usage', '=', 'inventory'),
                ('name', 'ilike', 'Inventory Loss')
            ], limit=1)
        if not location:
            raise UserError(_(
                "Inventory Loss location not found. "
                "Please create a location with usage 'Inventory Loss'."
            ))
        return location
    
    @api.model
    def create_hospitality_transfer(self, lines, employee_name):
        """
        Create an internal transfer for hospitality expense.
        
        This method is called from the POS frontend via RPC. It creates
        a stock picking that moves products from the main warehouse to
        the inventory loss location, recording it as a hospitality expense.
        
        Args:
            lines (list): List of dictionaries containing:
                - product_id (int): Product ID
                - name (str): Product display name
                - qty (float): Quantity to transfer
                - uom_id (int): Unit of measure ID
            employee_name (str): Name of the employee receiving the expense
            
        Returns:
            dict: Dictionary with status and reference
            
        Raises:
            UserError: If validation fails or transfer cannot be created
        """
        # Validate inputs
        if not lines:
            raise UserError(_("No products selected for hospitality expense."))
        
        if not employee_name or not employee_name.strip():
            raise UserError(_("Employee name is required."))
        
        if len(lines) > 100:
            raise UserError(_("Maximum 100 products allowed per expense."))
        
        # Create expense record
        expense = self.create({
            'employee_name': employee_name.strip(),
            'state': 'draft',
        })
        
        try:
            # Get locations and picking type
            picking_type = self._get_picking_type_internal()
            source_location = self._get_source_location()
            dest_location = self._get_destination_location()
            
            # Create stock picking
            picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': source_location.id,
                'location_dest_id': dest_location.id,
                'origin': f'Hospitality Expense - {employee_name.strip()}',
                'note': _(
                    "Hospitality expense for employee: %(emp)s\n"
                    "Expense Reference: %(ref)s",
                    emp=employee_name.strip(),
                    ref=expense.reference
                ),
            })
            
            # Update expense with picking reference
            expense.write({'picking_id': picking.id})
            
            # Create stock moves for each line
            for idx, line in enumerate(lines):
                product_id = line.get('product_id')
                qty = line.get('qty', 1.0)
                uom_id = line.get('uom_id')
                name = line.get('name', '')
                
                if not product_id:
                    raise UserError(_("Product ID is required for line %d.", idx + 1))
                
                product = self.env['product.product'].browse(product_id)
                if not product.exists():
                    raise UserError(_(
                        "Product not found for line %d: %s",
                        idx + 1, name or str(product_id)
                    ))
                
                # Get UoM
                if uom_id:
                    uom = self.env['uom.uom'].browse(uom_id)
                else:
                    uom = product.uom_id
                
                # Create stock move
                self.env['stock.move'].create({
                    'name': name or product.display_name,
                    'product_id': product_id,
                    'product_uom_qty': qty,
                    'product_uom': uom.id,
                    'location_id': source_location.id,
                    'location_dest_id': dest_location.id,
                    'picking_id': picking.id,
                })
                
                # Create expense line
                self.env['pos.hospitality.expense.line'].create({
                    'expense_id': expense.id,
                    'product_id': product_id,
                    'product_uom_id': uom.id,
                    'quantity': qty,
                })
            
            # Confirm and validate the picking
            picking.action_confirm()
            picking.action_assign()
            
            # Check if all moves are available
            for move in picking.move_ids:
                if move.state == 'confirmed':
                    move.force_assign()
            
            # Validate the picking (auto-assign if not done)
            picking.button_validate()
            
            # Mark expense as done
            expense.write({'state': 'done'})
            
            return {
                'status': 'success',
                'message': _(
                    'Hospitality expense recorded successfully!\n'
                    'Reference: %s\n'
                    'Employee: %s',
                    expense.reference,
                    employee_name.strip()
                ),
                'expense_id': expense.id,
                'reference': expense.reference,
            }
            
        except UserError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            # Rollback expense creation on error
            if expense:
                expense.unlink()
            raise UserError(_(
                "An error occurred while creating the hospitality expense: %s",
                str(e)
            ))


class PosHospitalityExpenseLine(models.Model):
    """
    Model for hospitality expense line items.
    """
    
    _name = "pos.hospitality.expense.line"
    _description = "POS Hospitality Expense Line"
    _rec_name = 'product_id'
    
    expense_id = fields.Many2one(
        'pos.hospitality.expense',
        string="Expense",
        required=True,
        ondelete='cascade',
        index=True
    )
    product_id = fields.Many2one(
        'product.product',
        string="Product",
        required=True,
        ondelete='restrict'
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
        digits='Product Unit of Measure'
    )
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set default UoM when product changes."""
        if self.product_id and not self.product_uom_id:
            self.product_uom_id = self.product_id.uom_id.id

