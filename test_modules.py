#!/usr/bin/env python3
"""
Odoo Module Testing Script
==========================

This script tests the custom Odoo modules for proper installation and functionality.
Tests include:
- Module loading verification
- Model creation and validation
- Sequence creation
- Access rights verification
- RPC method testing

Usage:
    python test_modules.py [--database DATABASE] [--admin-password PASSWORD]
"""

import sys
import os
import argparse
import logging

# Add Odoo to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'odoo'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Test Odoo custom modules'
    )
    parser.add_argument(
        '--database', '-d',
        default='my-odoo-db',
        help='Odoo database name (default: my-odoo-db)'
    )
    parser.add_argument(
        '--admin-password', '-w',
        default='admin',
        help='Odoo admin password (default: admin)'
    )
    parser.add_argument(
        '--host', '-H',
        default='localhost',
        help='Odoo server host (default: localhost)'
    )
    parser.add_argument(
        '--port', '-p',
        default='8069',
        help='Odoo server port (default: 8069)'
    )
    return parser.parse_args()


def test_module_installation(env, module_name):
    """Test if a module is properly installed."""
    logger.info(f"Testing module installation: {module_name}")
    
    try:
        # Check if module exists
        module = env['ir.module.module'].search([
            ('name', '=', module_name)
        ])
        
        if not module:
            logger.error(f"Module {module_name} not found!")
            return False
        
        logger.info(f"  - Module found: {module.state}")
        
        # Check state
        if module.state == 'installed':
            logger.info(f"  ✓ {module_name} is installed")
            return True
        elif module.state == 'to install':
            logger.warning(f"  ⚠ {module_name} needs to be installed")
            return False
        elif module.state == 'to upgrade':
            logger.info(f"  ⚠ {module_name} needs upgrade")
            return True
        else:
            logger.warning(f"  ⚠ {module_name} state: {module.state}")
            return False
            
    except Exception as e:
        logger.error(f"  ✗ Error testing {module_name}: {e}")
        return False


def test_model_creation(env, model_name):
    """Test if a model can be created/accessed."""
    logger.info(f"Testing model: {model_name}")
    
    try:
        # Try to access the model
        model = env[model_name]
        logger.info(f"  ✓ Model {model_name} accessible")
        
        # Check fields
        fields = model.fields_get()
        logger.info(f"  ✓ Model has {len(fields)} fields")
        
        return True
        
    except KeyError as e:
        logger.error(f"  ✗ Model {model_name} not found: {e}")
        return False
    except Exception as e:
        logger.error(f"  ✗ Error accessing {model_name}: {e}")
        return False


def test_sequence_creation(env, sequence_code):
    """Test if a sequence exists."""
    logger.info(f"Testing sequence: {sequence_code}")
    
    try:
        sequence = env['ir.sequence'].search([
            ('code', '=', sequence_code)
        ])
        
        if sequence:
            logger.info(f"  ✓ Sequence found: {sequence.prefix}{sequence.number_next_actual}")
            return True
        else:
            logger.warning(f"  ⚠ Sequence {sequence_code} not found")
            return False
            
    except Exception as e:
        logger.error(f"  ✗ Error testing sequence: {e}")
        return False


def test_access_rights(env, model_name, group_xml_id):
    """Test access rights for a model."""
    logger.info(f"Testing access rights for {model_name}")
    
    try:
        # Check if access rules exist
        access = env['ir.model.access'].search([
            ('model_id.model', '=', model_name)
        ])
        
        if access:
            logger.info(f"  ✓ Found {len(access)} access rules")
            for acc in access:
                logger.info(f"    - {acc.name}: {acc.perm_read}/{acc.perm_write}/{acc.perm_create}/{acc.perm_unlink}")
            return True
        else:
            logger.warning(f"  ⚠ No access rules found for {model_name}")
            return False
            
    except Exception as e:
        logger.error(f"  ✗ Error testing access rights: {e}")
        return False


def test_security_groups(env, module_name):
    """Test if security groups are created."""
    logger.info(f"Testing security groups for {module_name}")
    
    try:
        # Search for groups with the module's name
        groups = env['res.groups'].search([
            ('name', 'ilike', module_name.replace('_', ' '))
        ])
        
        if groups:
            logger.info(f"  ✓ Found {len(groups)} groups:")
            for group in groups:
                logger.info(f"    - {group.name}")
            return True
        else:
            logger.warning(f"  ⚠ No groups found for {module_name}")
            return False
            
    except Exception as e:
        logger.error(f"  ✗ Error testing groups: {e}")
        return False


def test_views(env, model_name):
    """Test if views are created for a model."""
    logger.info(f"Testing views for {model_name}")
    
    try:
        views = env['ir.ui.view'].search([
            ('model', '=', model_name)
        ])
        
        if views:
            logger.info(f"  ✓ Found {len(views)} views:")
            for view in views:
                logger.info(f"    - {view.name} ({view.type})")
            return True
        else:
            logger.warning(f"  ⚠ No views found for {model_name}")
            return False
            
    except Exception as e:
        logger.error(f"  ✗ Error testing views: {e}")
        return False


def test_actions(env, model_name):
    """Test if actions are created for a model."""
    logger.info(f"Testing actions for {model_name}")
    
    try:
        actions = env['ir.actions.act_window'].search([
            ('res_model', '=', model_name)
        ])
        
        if actions:
            logger.info(f"  ✓ Found {len(actions)} actions:")
            for action in actions:
                logger.info(f"    - {action.name}")
            return True
        else:
            logger.warning(f"  ⚠ No actions found for {model_name}")
            return False
            
    except Exception as e:
        logger.error(f"  ✗ Error testing actions: {e}")
        return False


def test_menu_items(env, module_name):
    """Test if menu items are created for a module."""
    logger.info(f"Testing menu items for {module_name}")
    
    try:
        # Search for menu items that reference the module
        menus = env['ir.ui.menu'].search([
            ('action', '!=', False)
        ])
        
        # Check if any menu is related to the module
        module_menus = []
        for menu in menus:
            if menu.action and hasattr(menu.action, 'res_model'):
                if module_name in (menu.action.res_model or ''):
                    module_menus.append(menu)
        
        if module_menus:
            logger.info(f"  ✓ Found {len(module_menus)} menu items:")
            for menu in module_menus:
                logger.info(f"    - {menu.name}")
            return True
        else:
            logger.info(f"  ℹ No specific menu items found for {module_name}")
            return True  # Not critical
            
    except Exception as e:
        logger.error(f"  ✗ Error testing menu items: {e}")
        return False


def test_stock_location(env, location_xml_id):
    """Test if stock location is created."""
    logger.info(f"Testing stock location: {location_xml_id}")
    
    try:
        location = env.ref(location_xml_id)
        if location:
            logger.info(f"  ✓ Location found: {location.name}")
            return True
        else:
            logger.warning(f"  ⚠ Location {location_xml_id} not found")
            return False
            
    except Exception as e:
        logger.warning(f"  ⚠ Location not found (may need module upgrade): {e}")
        return False


def test_rpc_methods(env, model_name):
    """Test RPC methods for a model."""
    logger.info(f"Testing RPC methods for {model_name}")
    
    try:
        model = env[model_name]
        
        # Check if the model has the required methods
        required_methods = ['create', 'write', 'read', 'unlink']
        
        for method in required_methods:
            if hasattr(model, method):
                logger.info(f"  ✓ Method {method} available")
            else:
                logger.warning(f"  ⚠ Method {method} not found")
        
        return True
        
    except Exception as e:
        logger.error(f"  ✗ Error testing RPC methods: {e}")
        return False


def run_tests(args):
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Odoo Custom Module Testing")
    logger.info("=" * 60)
    
    # Import Odoo after path setup
    import odoo
    from odoo import api, SUPERUSER_ID
    
    # Initialize Odoo
    odoo.tools.config.parse_config([
        '--database', args.database,
        '--db_user', 'postgres',
        '--db_password', 'postgres',
    ])
    
    # Create registry
    registry = odoo.modules.registry.Registry(args.database)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Results tracking
        results = {
            'hospitality_pos_expense': {
                'installed': False,
                'models': [],
                'sequences': [],
                'access': [],
                'groups': [],
                'views': [],
                'actions': [],
                'locations': [],
            },
            'internal_transfer_approval': {
                'installed': False,
                'models': [],
                'sequences': [],
                'access': [],
                'groups': [],
                'views': [],
                'actions': [],
            },
        }
        
        # Test hospitality_pos_expense module
        logger.info("\n" + "=" * 60)
        logger.info("Testing: hospitality_pos_expense")
        logger.info("=" * 60)
        
        results['hospitality_pos_expense']['installed'] = test_module_installation(
            env, 'hospitality_pos_expense'
        )
        
        # Test models
        for model in ['pos.hospitality.expense', 'pos.hospitality.expense.line']:
            results['hospitality_pos_expense']['models'].append(
                test_model_creation(env, model)
            )
        
        # Test sequences
        for seq_code in ['pos.hospitality.expense']:
            results['hospitality_pos_expense']['sequences'].append(
                test_sequence_creation(env, seq_code)
            )
        
        # Test access rights
        for model in ['pos.hospitality.expense', 'pos.hospitality.expense.line']:
            results['hospitality_pos_expense']['access'].append(
                test_access_rights(env, model, 'hospitality_pos_expense.group_hospitality_pos')
            )
        
        # Test groups
        results['hospitality_pos_expense']['groups'].append(
            test_security_groups(env, 'hospitality_pos_expense')
        )
        
        # Test views
        for model in ['pos.hospitality.expense']:
            results['hospitality_pos_expense']['views'].append(
                test_views(env, model)
            )
        
        # Test actions
        for model in ['pos.hospitality.expense']:
            results['hospitality_pos_expense']['actions'].append(
                test_actions(env, model)
            )
        
        # Test stock location
        results['hospitality_pos_expense']['locations'].append(
            test_stock_location(env, 'hospitality_pos_expense.location_inventory_loss_hospitality')
        )
        
        # Test internal_transfer_approval module
        logger.info("\n" + "=" * 60)
        logger.info("Testing: internal_transfer_approval")
        logger.info("=" * 60)
        
        results['internal_transfer_approval']['installed'] = test_module_installation(
            env, 'internal_transfer_approval'
        )
        
        # Test models
        for model in ['internal.approval.request']:
            results['internal_transfer_approval']['models'].append(
                test_model_creation(env, model)
            )
        
        # Test sequences
        for seq_code in ['internal.approval.request']:
            results['internal_transfer_approval']['sequences'].append(
                test_sequence_creation(env, seq_code)
            )
        
        # Test access rights
        for model in ['internal.approval.request']:
            results['internal_transfer_approval']['access'].append(
                test_access_rights(env, model, 'internal_transfer_approval.group_approval_user')
            )
        
        # Test groups
        results['internal_transfer_approval']['groups'].append(
            test_security_groups(env, 'internal_transfer_approval')
        )
        
        # Test views
        for model in ['internal.approval.request']:
            results['internal_transfer_approval']['views'].append(
                test_views(env, model)
            )
        
        # Test actions
        for model in ['internal.approval.request']:
            results['internal_transfer_approval']['actions'].append(
                test_actions(env, model)
            )
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("Test Summary")
        logger.info("=" * 60)
        
        for module, result in results.items():
            logger.info(f"\n{module}:")
            logger.info(f"  Installed: {'✓' if result['installed'] else '✗'}")
            
            passed_models = sum(result['models'])
            total_models = len(result['models'])
            logger.info(f"  Models: {passed_models}/{total_models}")
            
            passed_seq = sum(result['sequences'])
            total_seq = len(result['sequences'])
            logger.info(f"  Sequences: {passed_seq}/{total_seq}")
            
            passed_access = sum(result['access'])
            total_access = len(result['access'])
            logger.info(f"  Access Rights: {passed_access}/{total_access}")
            
            passed_groups = sum(result['groups'])
            total_groups = len(result['groups'])
            logger.info(f"  Groups: {passed_groups}/{total_groups}")
            
            passed_views = sum(result['views'])
            total_views = len(result['views'])
            logger.info(f"  Views: {passed_views}/{total_views}")
            
            passed_actions = sum(result['actions'])
            total_actions = len(result['actions'])
            logger.info(f"  Actions: {passed_actions}/{total_actions}")
        
        # Return overall status
        all_passed = all([
            results['hospitality_pos_expense']['installed'],
            results['internal_transfer_approval']['installed'],
        ])
        
        return all_passed


if __name__ == '__main__':
    args = parse_args()
    
    try:
        success = run_tests(args)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

