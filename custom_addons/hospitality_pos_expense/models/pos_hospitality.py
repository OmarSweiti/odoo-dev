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
- Automatic accounting entries in Hospitality Expense account
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
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        readonly=True,
        default=lambda self: self.env.company
    )
    note = fields.Text(
        string="Notes",
        help="Additional notes for this hospitality expense"
    )
    account_move_id = fields.Many2one(
        'account.move',
        string="Journal Entry",
        readonly=True,
        copy=False,
        help="The accounting journal entry created for this expense"
    )
    
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
        # First try to get the location from our module's XML ID
        location = self.env.ref(
            'hospitality_pos_expense.location_inventory_loss_hospitality',
            raise_if_not_found=False
        )
        if location:
            return location
        
        # Fallback 1: Search for our location by name
        location = self.env['stock.location'].search([
            ('name', '=', 'Inventory Loss (Hospitality)'),
            ('usage', '=', 'inventory'),
        ], limit=1)
        if location:
            return location
        
        # Fallback 2: Search for any inventory loss type location
        location = self.env['stock.location'].search([
            ('name', 'ilike', 'Inventory Loss'),
            ('usage', '=', 'inventory'),
        ], limit=1)
        if location:
            return location
        
        # Fallback 3: Search for virtual locations
        location = self.env['stock.location'].search([
            ('usage', '=', 'view'),
            ('name', 'ilike', 'Virtual'),
        ], limit=1)
        if location:
            # Create a child location under Virtual Locations
            location = self.env['stock.location'].create({
                'name': 'Inventory Loss (Hospitality)',
                'usage': 'inventory',
                'location_id': location.id,
                'company_id': self.env.company.id,
                'barcode': 'INV_LOSS_HOSP',
            })
            return location
        
        raise UserError(_(
            "No suitable location found. Please create a location with "
            "usage 'Inventory Loss' or 'Virtual' for hospitality expenses."
        ))
    
    def _get_hospitality_expense_account(self):
        """
        Get the Hospitality Expense account.
        
        Returns:
            Recordset: The account.account record for hospitality expenses
        """
        account = self.env.ref(
            'hospitality_pos_expense.account_hospitality_expense',
            raise_if_not_found=False
        )
        if account:
            return account
        
        # Fallback: Search by code
        account = self.env['account.account'].search([
            ('code', '=', '610500'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if account:
            return account
        
        # Fallback: Search by name
        account = self.env['account.account'].search([
            ('name', 'ilike', 'Hospitality Expense'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if account:
            return account
        
        raise UserError(_(
            "Hospitality Expense account not found. "
            "Please configure account 610500 or create an account named 'Hospitality Expense'."
        ))
    
    def _get_stock_input_account(self, product):
        """
        Get the stock input account for the product.
        
        Args:
            product: The product.product record
            
        Returns:
            Recordset: The stock input account
        """
        # Get the stock valuation account from product
        if product.categ_id.property_stock_valuation_account_id:
            return product.categ_id.property_stock_valuation_account_id
        
        # Fallback to default accounts
        if product.categ_id.property_stock_account_input_categ_id:
            return product.categ_id.property_stock_account_input_categ_id
        
        # Search for stock input account
        accounts = self.env['account.account'].search([
            ('code', 'like', '14%'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if accounts:
            return accounts
        
        raise UserError(_(
            "Stock valuation account not found for product %s. "
            "Please configure product category accounts.",
            product.display_name
        ))
    
    def _create_account_moves(self, expense, picking):
        """
        Create accounting journal entries for the hospitality expense.
        
        Creates:
        - Credit entry to stock valuation (removing inventory value)
        - Debit entry to hospitality expense account
        
        Args:
            expense: The hospitality expense record
            picking: The stock picking record
            
        Returns:
            Recordset: The created account.move record
        """
        if not self.env.company.country_id:
            raise UserError(_("Please set the company country in settings."))
        
        move_lines = []
        total_cost = 0.0
        
        # Get expense account
        expense_account = self._get_hospitality_expense_account()
        
        for line in expense.line_ids:
            product = line.product_id
            qty = line.quantity
            cost = line.standard_price * qty
            total_cost += cost
            
            # Get stock valuation account for this product
            stock_account = self._get_stock_input_account(product)
            
            # Create move line for stock valuation (credit)
            move_lines.append((0, 0, {
                'name': _("%(product)s - Stock out for hospitality", product=product.display_name),
                'account_id': stock_account.id,
                'debit': 0.0,
                'credit': cost,
                'product_id': product.id,
                'quantity': qty,
                'company_id': self.env.company.id,
            }))
            
            # Create move line for hospitality expense (debit)
            move_lines.append((0, 0, {
                'name': _("%(product)s - Hospitality expense for %(employee)s",
                         product=product.display_name,
                         employee=expense.employee_name),
                'account_id': expense_account.id,
                'debit': cost,
                'credit': 0.0,
                'product_id': product.id,
                'quantity': qty,
                'company_id': self.env.company.id,
            }))
        
        if not move_lines:
            return None
        
        # Create the journal entry
        move = self.env['account.move'].create({
            'move_type': 'entry',
            'ref': _("%(ref)s - Hospitality expense for %(employee)s",
                    ref=expense.reference,
                    employee=expense.employee_name),
            'journal_id': self.env['account.journal'].search([
                ('type', '=', 'general'),
                ('company_id', '=', self.env.company.id),
            ], limit=1).id,
            'line_ids': move_lines,
            'company_id': self.env.company.id,
            'date': fields.Date.today(),
        })
        
        # Post the move
        move.action_post()
        
        return move
    
    @api.model
    def create_hospitality_transfer(self, lines, employee_name):
        """
        Create an internal transfer for hospitality expense.
        
        This method is called from the POS frontend via RPC. It creates
        a stock picking that moves products from the main warehouse to
        the inventory loss location, recording it as a hospitality expense.
        It also creates accounting journal entries for cost tracking.
        
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
                'company_id': self.env.company.id,
            })
            
            # Update expense with picking reference
            expense.write({'picking_id': picking.id})
            
            # Create stock moves and expense lines for each product
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
                move = self.env['stock.move'].create({
                    'name': name or product.display_name,
                    'product_id': product_id,
                    'product_uom_qty': qty,
                    'product_uom': uom.id,
                    'location_id': source_location.id,
                    'location_dest_id': dest_location.id,
                    'picking_id': picking.id,
                    'company_id': self.env.company.id,
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
            
            # Create stock move lines for each move (immediate transfer)
            for move in picking.move_ids:
                if move.state in ('confirmed', 'assigned'):
                    move.quantity_done = move.product_uom_qty
                    # Create move line with the full quantity
                    self.env['stock.move.line'].create({
                        'move_id': move.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'picking_id': move.picking_id.id,
                        'qty_done': move.product_uom_qty,
                        'company_id': move.company_id.id,
                    })
            
            # Validate the picking (auto-assign if not done)
            picking.button_validate()
            
            # Create accounting journal entries for the expense
            move = self._create_account_moves(expense, picking)
            if move:
                expense.write({'account_move_id': move.id})
            
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
    
    def action_view_journal_entry(self):
        """
        Open the associated journal entry.
        
        Returns:
            dict: Window action to open the journal entry
        """
        self.ensure_one()
        if not self.account_move_id:
            raise UserError(_("No journal entry associated with this expense."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.account_move_id.id,
            'target': 'current',
        }


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
    product_tmpl_id = fields.Many2one(
        'product.template',
        string="Product Template",
        related='product_id.product_tmpl_id',
        readonly=True
    )
    standard_price = fields.Float(
        string="Standard Cost",
        related='product_id.standard_price',
        readonly=True
    )
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set default UoM when product changes."""
        if self.product_id and not self.product_uom_id:
            self.product_uom_id = self.product_id.uom_id.id
    
    @api.depends('quantity', 'standard_price')
    def _compute_total_cost(self):
        """Calculate total cost for the line."""
        for line in self:
            line.total_cost = line.quantity * line.standard_price
    
    total_cost = fields.Float(
        string="Total Cost",
        compute='_compute_total_cost',
        store=False
    )

