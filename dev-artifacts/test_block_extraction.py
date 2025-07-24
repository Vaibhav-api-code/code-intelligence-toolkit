#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Test file for demonstrating block extraction capabilities."""

Author: Vaibhav-api-code
Co-Author: Claude Code (https://claude.ai/code)
Created: 2025-07-21
Updated: 2025-07-23
License: Mozilla Public License 2.0 (MPL-2.0)
"""

def process_order(order_id, items, customer):
    """Process an order with multiple items."""
    total = 0
    
    # Multi-line conditional with nested blocks
    if (customer.is_premium and 
        len(items) > 5 and
        customer.credit_score > 700):
        
        discount = 0.15
        print(f"Premium customer {customer.name} gets {discount * 100}% discount")
        
        for item in items:
            if item.in_stock:
                price = item.price * (1 - discount)
                total += price
                
                # Nested try block
                try:
                    item.reserve()
                    print(f"Reserved {item.name}")
                except StockError as e:
                    print(f"Failed to reserve {item.name}: {e}")
                    continue
            else:
                print(f"Item {item.name} is out of stock")
    
    # Multi-line method call
    result = send_order_confirmation(
        customer_email=customer.email,
        order_id=order_id,
        items=[item.name for item in items if item.in_stock],
        total_amount=total,
        estimated_delivery=calculate_delivery_date(customer.location),
        tracking_enabled=True
    )
    
    return result


class OrderProcessor:
    def validate_order(self, order):
        """Validate order with complex conditions."""
        
        # Multi-line conditional
        if (order.total > 1000 or
            order.customer.is_vip or
            (order.items_count > 10 and 
             order.shipping_method == 'express')):
            
            # Complex validation logic
            validation_errors = []
            
            for item in order.items:
                if not item.is_valid():
                    validation_errors.append(f"Invalid item: {item.id}")
            
            if validation_errors:
                raise ValidationError(
                    f"Order {order.id} failed validation",
                    errors=validation_errors,
                    order_id=order.id
                )
        
        return True
    
    def process_payment(self, order, payment_info):
        """Process payment with error handling."""
        
        try:
            # Multi-step payment process
            payment_token = self.tokenize_payment(payment_info)
            
            charge_result = self.payment_gateway.charge(
                amount=order.total,
                currency=order.currency,
                token=payment_token,
                metadata={
                    'order_id': order.id,
                    'customer_id': order.customer.id,
                    'items': len(order.items)
                }
            )
            
            if charge_result.success:
                order.mark_paid()
                return True
            else:
                # Handle payment failure
                self.handle_payment_failure(
                    order=order,
                    reason=charge_result.failure_reason,
                    attempt_number=order.payment_attempts + 1
                )
                return False
                
        except PaymentGatewayError as e:
            # Log and re-raise
            self.logger.error(f"Payment gateway error for order {order.id}: {e}")
            raise
        
        except Exception as e:
            # Catch-all for unexpected errors
            self.logger.error(f"Unexpected error processing payment: {e}")
            order.mark_payment_failed()
            raise


# Example of standalone multi-line statement
analysis_results = analyze_customer_behavior(
    customer_id=customer.id,
    time_range=DateRange(
        start=datetime.now() - timedelta(days=90),
        end=datetime.now()
    ),
    metrics=['purchase_frequency', 'average_order_value', 'category_preferences'],
    include_predictions=True,
    confidence_threshold=0.85
)