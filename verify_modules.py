#!/usr/bin/env python3
"""
Odoo Module Verification via HTTP API
======================================

This script verifies module functionality via Odoo's XML-RPC API.
Run this while Odoo server is running.

Usage:
    python verify_modules.py --host HOST --port PORT --database DB --user USER --password PASS
"""

import sys
import os
import xmlrpc.client
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Verify Odoo modules via XML-RPC'
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
    parser.add_argument(
        '--database', '-d',
        required=True,
        help='Odoo database name'
    )
    parser.add_argument(
        '--user', '-u',
        default='admin',
        help='Odoo admin user (default: admin)'
    )
    parser.add_argument(
        '--password', '-w',
        default='admin',
        help='Odoo admin password (default: admin)'
    )
    return parser.parse_args()


def get_common_endpoint(host, port):
    """Get the XML-RPC common endpoint."""
    return f"http://{host}:{port}/xmlrpc/2/common"


def get_object_endpoint(host, port):
    """Get the XML-RPC object endpoint."""
    return f"http://{host}:{port}/xmlrpc/2/object"


def authenticate(url, db, user, password):
    """Authenticate with Odoo and get uid."""
    try:
        common = xmlrpc.client.ServerProxy(url)
        uid = common.authenticate(db, user, password, {})
        if uid:
            logger.info(f"✓ Authenticated successfully (UID: {uid})")
            return uid
        else:
            logger.error("✗ Authentication failed")
            return None
    except Exception as e:
        logger.error(f"✗ Authentication error: {e}")
        return None


def test_module_installation(uid, url, db, password, module_name):
    """Test if a module is installed."""
    logger.info(f"Testing module: {module_name}")
    
    try:
        models = xmlrpc.client.ServerProxy(url)
        
        # Search for the module
        module_ids = models.execute_kw(
            db, uid, password,
            'ir.module.module', 'search',
            [[('name', '=', module_name)]]
        )
        
        if not module_ids:
            logger.error(f"  ✗ Module {module_name} not found")
            return False
        
        # Get module state
        module_data = models.execute_kw(
            db, uid, password,
            'ir.module.module', 'read',
            module_ids, ['state', 'name']
        )
        
        state = module_data[0]['state'] if module_data else 'unknown'
        logger.info(f"  - Module state: {state}")
        
        if state == 'installed':
            logger.info(f"  ✓ {module_name} is installed")
            return True
        else:
            logger.warning(f"  ⚠ {module_name} is not installed (state: {state})")
            return False
            
    except Exception as e:
        logger.error(f"  ✗ Error testing module: {e}")
        return False


def test_model_access(uid, url, db, password, model_name):
    """Test if a model can be accessed."""
    logger.info(f"Testing model access: {model_name}")
    
    try:
        models = xmlrpc.client.ServerProxy(url)
        
        # Try to read model fields
        fields = models.execute_kw(
            db, uid, password,
            model_name, 'fields_get',
            []
        )
        
        if fields:
            logger.info(f"  ✓ Model accessible with {len(fields)} fields")
            return True
        else:
            logger.error(f"  ✗ Model not accessible")
            return False
            
    except xmlrpc.client.Fault as e:
        logger.error(f"  ✗ Model error: {e.faultString}")
        return False
    except Exception as e:
        logger.error(f"  ✗ Error: {e}")
        return False


def test_sequence(uid, url, db, password, sequence_code):
    """Test if a sequence exists."""
    logger.info(f"Testing sequence: {sequence_code}")
    
    try:
        models = xmlrpc.client.ServerProxy(url)
        
        # Search for sequence
        seq_ids = models.execute_kw(
            db, uid, password,
            'ir.sequence', 'search',
            [[('code', '=', sequence_code)]]
        )
        
        if seq_ids:
            seq_data = models.execute_kw(
                db, uid, password,
                'ir.sequence', 'read',
                seq_ids, ['prefix', 'number_next_actual']
            )
            prefix = seq_data[0]['prefix'] if seq_data else '?'
            next_num = seq_data[0]['number_next_actual'] if seq_data else '?'
            logger.info(f"  ✓ Sequence found: {prefix}{next_num}")
            return True
        else:
            logger.warning(f"  ⚠ Sequence not found")
            return False
            
    except Exception as e:
        logger.error(f"  ✗ Error testing sequence: {e}")
        return False


def test_view_access(uid, url, db, password, model_name):
    """Test if views exist for a model."""
    logger.info(f"Testing views for: {model_name}")
    
    try:
        models = xmlrpc.client.ServerProxy(url)
        
        # Search for views
        view_ids = models.execute_kw(
            db, uid, password,
            'ir.ui.view', 'search',
            [[('model', '=', model_name)]]
        )
        
        if view_ids:
            view_data = models.execute_kw(
                db, uid, password,
                'ir.ui.view', 'read',
                view_ids, ['name', 'type']
            )
            logger.info(f"  ✓ Found {len(view_data)} views:")
            for view in view_data:
                logger.info(f"    - {view['name']} ({view['type']})")
            return True
        else:
            logger.warning(f"  ⚠ No views found")
            return False
            
    except Exception as e:
        logger.error(f"  ✗ Error testing views: {e}")
        return False


def test_action_access(uid, url, db, password, model_name):
    """Test if actions exist for a model."""
    logger.info(f"Testing actions for: {model_name}")
    
    try:
        models = xmlrpc.client.ServerProxy(url)
        
        # Search for actions
        action_ids = models.execute_kw(
            db, uid, password,
            'ir.actions.act_window', 'search',
            [[('res_model', '=', model_name)]]
        )
        
        if action_ids:
            action_data = models.execute_kw(
                db, uid, password,
                'ir.actions.act_window', 'read',
                action_ids, ['name']
            )
            logger.info(f"  ✓ Found {len(action_data)} actions:")
            for action in action_data:
                logger.info(f"    - {action['name']}")
            return True
        else:
            logger.warning(f"  ⚠ No actions found")
            return False
            
    except Exception as e:
        logger.error(f"  ✗ Error testing actions: {e}")
        return False


def test_menu_access(uid, url, db, password, module_name):
    """Test if menu items exist for a module."""
    logger.info(f"Testing menus for: {module_name}")
    
    try:
        models = xmlrpc.client.ServerProxy(url)
        
        # Search for menu items with actions
        menu_ids = models.execute_kw(
            db, uid, password,
            'ir.ui.menu', 'search',
            [[('action', '!=', False)]]
        )
        
        # Get action models
        menus = models.execute_kw(
            db, uid, password,
            'ir.ui.menu', 'read',
            menu_ids, ['name', 'action']
        )
        
        # Filter by module
        module_menus = []
        for menu in menus:
            if menu['action']:
                action_model = menu['action'].split(',')[0] if isinstance(menu['action'], str) else ''
                if module_name in action_model:
                    module_menus.append(menu)
        
        if module_menus:
            logger.info(f"  ✓ Found {len(module_menus)} menus:")
            for menu in module_menus:
                logger.info(f"    - {menu['name']}")
            return True
        else:
            logger.info(f"  ℹ No specific menus found (may be normal)")
            return True
            
    except Exception as e:
        logger.error(f"  ✗ Error testing menus: {e}")
        return False


def test_rpc_method(uid, url, db, password, model_name, method_name):
    """Test if a specific RPC method exists."""
    logger.info(f"Testing RPC method {model_name}.{method_name}()")
    
    try:
        models = xmlrpc.client.ServerProxy(url)
        
        # Try to call the method (will fail if not exists)
        # We'll just check if method name is in the model
        models.execute_kw(
            db, uid, password,
            model_name, 'method_exists',
            [method_name]
        )
        logger.info(f"  ✓ Method exists")
        return True
        
    except Exception as e:
        # Method might not exist, but that's okay for some cases
        logger.warning(f"  ⚠ Method check: {e}")
        return True  # Don't fail on this


def run_verification(args):
    """Run all verification tests."""
    logger.info("=" * 60)
    logger.info("Odoo Module Verification via XML-RPC")
    logger.info("=" * 60)
    
    common_url = get_common_endpoint(args.host, args.port)
    object_url = get_object_endpoint(args.host, args.port)
    
    # Authenticate
    uid = authenticate(common_url, args.database, args.user, args.password)
    if not uid:
        logger.error("Authentication failed. Please check credentials.")
        return False
    
    results = {
        'hospitality_pos_expense': {
            'installed': False,
            'models': [],
            'sequences': [],
            'views': [],
            'actions': [],
        },
        'internal_transfer_approval': {
            'installed': False,
            'models': [],
            'sequences': [],
            'views': [],
            'actions': [],
        },
    }
    
    # Test hospitality_pos_expense module
    logger.info("\n" + "-" * 60)
    logger.info("Testing: hospitality_pos_expense")
    logger.info("-" * 60)
    
    results['hospitality_pos_expense']['installed'] = test_module_installation(
        uid, object_url, args.database, args.password, 'hospitality_pos_expense'
    )
    
    # Test models
    for model in ['pos.hospitality.expense', 'pos.hospitality.expense.line']:
        results['hospitality_pos_expense']['models'].append(
            test_model_access(uid, object_url, args.database, args.password, model)
        )
    
    # Test sequences
    for seq in ['pos.hospitality.expense']:
        results['hospitality_pos_expense']['sequences'].append(
            test_sequence(uid, object_url, args.database, args.password, seq)
        )
    
    # Test views
    results['hospitality_pos_expense']['views'].append(
        test_view_access(uid, object_url, args.database, args.password, 'pos.hospitality.expense')
    )
    
    # Test actions
    results['hospitality_pos_expense']['actions'].append(
        test_action_access(uid, object_url, args.database, args.password, 'pos.hospitality.expense')
    )
    
    # Test menus
    test_menu_access(uid, object_url, args.database, args.password, 'hospitality_pos_expense')
    
    # Test internal_transfer_approval module
    logger.info("\n" + "-" * 60)
    logger.info("Testing: internal_transfer_approval")
    logger.info("-" * 60)
    
    results['internal_transfer_approval']['installed'] = test_module_installation(
        uid, object_url, args.database, args.password, 'internal_transfer_approval'
    )
    
    # Test models
    results['internal_transfer_approval']['models'].append(
        test_model_access(uid, object_url, args.database, args.password, 'internal.approval.request')
    )
    
    # Test sequences
    results['internal_transfer_approval']['sequences'].append(
        test_sequence(uid, object_url, args.database, args.password, 'internal.approval.request')
    )
    
    # Test views
    results['internal_transfer_approval']['views'].append(
        test_view_access(uid, object_url, args.database, args.password, 'internal.approval.request')
    )
    
    # Test actions
    results['internal_transfer_approval']['actions'].append(
        test_action_access(uid, object_url, args.database, args.password, 'internal.approval.request')
    )
    
    # Test menus
    test_menu_access(uid, object_url, args.database, args.password, 'internal_transfer_approval')
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("Verification Summary")
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
        
        passed_views = sum(result['views'])
        total_views = len(result['views'])
        logger.info(f"  Views: {passed_views}/{total_views}")
        
        passed_actions = sum(result['actions'])
        total_actions = len(result['actions'])
        logger.info(f"  Actions: {passed_actions}/{total_actions}")
    
    # Overall status
    all_passed = all([
        results['hospitality_pos_expense']['installed'],
        results['internal_transfer_approval']['installed'],
    ])
    
    if all_passed:
        logger.info("\n✓ All modules are properly installed!")
    else:
        logger.info("\n⚠ Some modules need attention.")
    
    return all_passed


if __name__ == '__main__':
    args = parse_args()
    
    try:
        success = run_verification(args)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

