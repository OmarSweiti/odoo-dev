/**
 * POS Hospitality Expense Button Module
 * 
 * This module adds a hospitality expense button to the POS interface,
 * allowing selected users to record employee meals as expenses instead of sales.
 * 
 * Features:
 * - Button visible only to users with 'hospitality_pos_expense.group_hospitality_pos' group
 * - Creates internal transfers from main warehouse to Inventory Loss
 * - Prompts for employee name before processing
 * - Generates accounting journal entries
 * - No invoice or sales record is generated
 */

// Import necessary components from Odoo POS
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

/**
 * HospitalityButton Component
 * 
 * A POS button that allows cashiers to record hospitality expenses.
 * Only visible to users with the 'hospitality_pos_expense.group_hospitality_pos' group.
 */
class HospitalityButton extends Component {
    /**
     * Setup the component with required services
     */
    setup() {
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.rpc = useService("rpc");
        this.action = useService("action");
    }

    /**
     * Get the current POS order
     */
    get currentOrder() {
        return this.env.pos.get_order();
    }

    /**
     * Check if button should be available
     * Button is available when there's an active order with products
     */
    get isAvailable() {
        const order = this.currentOrder;
        return order && order.get_orderlines().length > 0;
    }

    /**
     * Handle button click event
     * Opens the employee selection and product confirmation dialogs
     */
    async onClick() {
        try {
            await this.processHospitalityExpense();
        } catch (error) {
            console.error("Hospitality expense error:", error);
            this.notification.add(
                error.message || _t("An error occurred while processing the expense."),
                {
                    type: "danger",
                    title: _t("Error"),
                }
            );
        }
    }

    /**
     * Process the hospitality expense workflow
     * 1. Get selected products from current order
     * 2. Prompt for employee name
     * 3. Confirm with user
     * 4. Create transfer via RPC
     */
    async processHospitalityExpense() {
        const order = this.currentOrder;
        
        if (!order) {
            this.notification.add(
                _t("No active order found."),
                { type: "warning", title: _t("Warning") }
            );
            return;
        }

        const lines = order.get_orderlines();
        
        if (lines.length === 0) {
            this.notification.add(
                _t("No products in the current order."),
                { type: "warning", title: _t("Warning") }
            );
            return;
        }

        // Prepare product data
        const products = lines.map((line) => ({
            product_id: line.product.id,
            name: line.product.display_name,
            qty: line.quantity,
            uom_id: line.product.uom_id?.id,
            price: line.product.lst_price,
            image_url: `/web/image?model=product.product&id=${line.product.id}&field=image_128`,
        }));

        // Show employee selection dialog
        const employeeResult = await this.showEmployeeDialog();
        if (!employeeResult || !employeeResult.confirmed) {
            return; // User cancelled
        }

        const employeeName = employeeResult.payload.employee_name?.trim();
        if (!employeeName) {
            this.notification.add(
                _t("Employee name is required."),
                { type: "warning", title: _t("Warning") }
            );
            return;
        }

        // Show confirmation dialog with product summary
        const confirmResult = await this.showConfirmationDialog(
            products,
            employeeName
        );
        if (!confirmResult || !confirmResult.confirmed) {
            return; // User cancelled
        }

        // Prepare data for RPC call
        const linesData = products.map((p) => ({
            product_id: p.product_id,
            name: p.name,
            qty: p.qty,
            uom_id: p.uom_id,
        }));

        // Create hospitality transfer via RPC
        this.notification.add(
            _t("Processing hospitality expense..."),
            { type: "info", title: _t("Processing") }
        );

        const result = await this.rpc({
            model: "pos.hospitality.expense",
            method: "create_hospitality_transfer",
            args: [linesData, employeeName],
        });

        if (result && result.status === "success") {
            // Destroy the current order after successful transfer
            order.destroy();

            this.notification.add(
                result.message || _t("Hospitality expense recorded successfully!"),
                { type: "success", title: _t("Success") }
            );
        } else {
            throw new Error(result?.message || _t("Failed to create expense."));
        }
    }

    /**
     * Show dialog to enter employee name
     * @returns {Promise<Object>} Dialog result with confirmed flag and payload
     */
    async showEmployeeDialog() {
        const TextInputPopup = await import("@point_of_sale/app/components/text_input_popup/text_input_popup");
        return new Promise((resolve) => {
            this.dialog.add(
                TextInputPopup,
                {
                    title: _t("Hospitality Expense"),
                    payload: {
                        inputPlaceholder: _t("Enter employee name"),
                    },
                    confirm: (payload) => {
                        resolve({ confirmed: true, payload });
                    },
                    cancel: () => {
                        resolve({ confirmed: false });
                    },
                }
            );
        });
    }

    /**
     * Show confirmation dialog with product summary
     * @param {Array} products - List of products in the order
     * @param {string} employeeName - Name of the employee
     * @returns {Promise<Object>} Dialog result with confirmed flag
     */
    async showConfirmationDialog(products, employeeName) {
        // Build product summary HTML
        const productList = products
            .map(
                (p) =>
                    `<li style="margin: 5px 0;">
                        <strong>${p.name}</strong> - Qty: ${p.qty.toFixed(2)}
                    </li>`
            )
            .join("");

        const totalItems = products.reduce((sum, p) => sum + p.qty, 0);
        const message = `
            <div style="padding: 10px;">
                <p><strong>Employee:</strong> ${employeeName}</p>
                <p><strong>Products:</strong> ${products.length} items (${totalItems} total)</p>
                <ul style="margin-top: 10px; padding-left: 20px;">
                    ${productList}
                </ul>
                <p style="margin-top: 15px; color: #666;">
                    <em>This will create an internal transfer to Inventory Loss location.</em>
                </p>
            </div>
        `;

        const ConfirmPopup = await import("@point_of_sale/app/components/confirm_popup/confirm_popup");
        return new Promise((resolve) => {
            this.dialog.add(
                ConfirmPopup,
                {
                    title: _t("Confirm Hospitality Expense"),
                    body: message,
                    confirmText: _t("Confirm"),
                    cancelText: _t("Cancel"),
                    confirm: () => {
                        resolve({ confirmed: true });
                    },
                    cancel: () => {
                        resolve({ confirmed: false });
                    },
                }
            );
        });
    }
}

// Set template for the component
HospitalityButton.template = "HospitalityButton";

// Register the button in the Product Screen
ProductScreen.addControlButton({
    component: HospitalityButton,
    condition: function () {
        // Check if current user has the hospitality group
        try {
            const cashier = this.env.pos.get_cashier();
            if (cashier && cashier.has_group) {
                return cashier.has_group(
                    "hospitality_pos_expense.group_hospitality_pos"
                );
            }
        } catch (error) {
            console.warn("Error checking group:", error);
        }
        
        // Fallback: check user groups directly via the user model
        const user = this.env.pos.user;
        if (user && user.groups_id) {
            // The groups_id might be a list of XML IDs or records
            const groupXmlId = "hospitality_pos_expense.group_hospitality_pos";
            
            // Check if any group matches
            for (const group of user.groups_id) {
                // If it's a string (XML ID)
                if (typeof group === 'string' && group.includes(groupXmlId)) {
                    return true;
                }
                // If it's an array [id, display_name, xml_id]
                if (Array.isArray(group) && group[2] === groupXmlId) {
                    return true;
                }
                // If it's a record with id
                if (group.id && typeof group.id === 'string' && group.id.includes(groupXmlId)) {
                    return true;
                }
            }
        }
        
        return false;
    },
    isAvailable: function () {
        // Button is available when there's an active order with products
        const order = this.env.pos.get_order();
        return order && order.get_orderlines().length > 0;
    },
});

