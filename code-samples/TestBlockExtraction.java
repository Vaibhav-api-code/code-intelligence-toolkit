/*
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/.
 * 
 * Multi-line conditional with complex logic
 * 
 * Author: Vaibhav-api-code
 * Co-Author: Claude Code (https://claude.ai/code)
 * Created: 2025-07-21
 * Updated: 2025-07-23
 * License: Mozilla Public License 2.0 (MPL-2.0)
 */
public class TestBlockExtraction {
    
    public void processOrder(String orderId, List<Item> items, Customer customer) {
        double total = 0;
        
        // Multi-line conditional with complex logic
        if (customer.isPremium() && 
            items.size() > 5 &&
            customer.getCreditScore() > 700 &&
            isEligibleForDiscount(customer)) {
            
            double discount = 0.15;
            System.out.println("Premium customer " + customer.getName() + 
                             " gets " + (discount * 100) + "% discount");
            
            for (Item item : items) {
                if (item.isInStock()) {
                    double price = item.getPrice() * (1 - discount);
                    total += price;
                    
                    // Nested try-catch block
                    try {
                        item.reserve();
                        System.out.println("Reserved " + item.getName());
                    } catch (StockException e) {
                        System.err.println("Failed to reserve " + item.getName() + 
                                         ": " + e.getMessage());
                        continue;
                    }
                } else {
                    System.out.println("Item " + item.getName() + " is out of stock");
                }
            }
        }
        
        // Multi-line method call
        OrderResult result = sendOrderConfirmation(
            customer.getEmail(),
            orderId,
            items.stream()
                .filter(Item::isInStock)
                .map(Item::getName)
                .collect(Collectors.toList()),
            total,
            calculateDeliveryDate(customer.getLocation()),
            true
        );
        
        // Complex switch statement
        switch (result.getStatus()) {
            case SUCCESS:
                notifyCustomer(customer, "Order confirmed!");
                scheduleDelivery(orderId, result.getDeliveryDate());
                break;
                
            case PARTIAL_SUCCESS:
                notifyCustomer(customer, 
                    "Some items in your order are unavailable. " +
                    "We'll process available items.");
                updateInventory(items);
                break;
                
            case FAILURE:
                handleOrderFailure(orderId, 
                    result.getFailureReason(),
                    customer);
                refundPayment(orderId);
                break;
                
            default:
                logError("Unknown order status: " + result.getStatus());
        }
    }
    
    private boolean validatePayment(Order order, PaymentInfo paymentInfo) {
        // Complex validation with multiple conditions
        if (paymentInfo.getCardNumber() != null &&
            paymentInfo.getCardNumber().length() == 16 &&
            paymentInfo.getExpiryDate().isAfter(LocalDate.now()) &&
            (paymentInfo.getCvv() != null && paymentInfo.getCvv().length() == 3)) {
            
            try {
                // Multi-step validation process
                PaymentToken token = tokenizePayment(paymentInfo);
                
                ChargeResult chargeResult = paymentGateway.charge(
                    new ChargeRequest.Builder()
                        .withAmount(order.getTotal())
                        .withCurrency(order.getCurrency())
                        .withToken(token)
                        .withMetadata(Map.of(
                            "orderId", order.getId(),
                            "customerId", order.getCustomerId(),
                            "itemCount", String.valueOf(order.getItems().size())
                        ))
                        .build()
                );
                
                if (chargeResult.isSuccess()) {
                    order.markPaid();
                    return true;
                } else {
                    // Handle payment failure
                    handlePaymentFailure(
                        order,
                        chargeResult.getFailureReason(),
                        order.getPaymentAttempts() + 1
                    );
                    return false;
                }
                
            } catch (PaymentGatewayException e) {
                logger.error("Payment gateway error for order " + order.getId(), e);
                throw e;
            } catch (Exception e) {
                logger.error("Unexpected error processing payment", e);
                order.markPaymentFailed();
                throw new RuntimeException("Payment processing failed", e);
            }
        }
        
        return false;
    }
    
    // Example of multi-line lambda expression
    private void processItems(List<Item> items) {
        items.stream()
            .filter(item -> item.getPrice() > 100 &&
                           item.getCategory().equals("ELECTRONICS") &&
                           item.getStock() > 0)
            .sorted((a, b) -> {
                int priceComparison = Double.compare(b.getPrice(), a.getPrice());
                if (priceComparison != 0) {
                    return priceComparison;
                }
                return a.getName().compareTo(b.getName());
            })
            .forEach(item -> {
                System.out.println("Processing high-value item: " + item.getName());
                updateInventory(item);
                notifyWarehouse(item);
            });
    }
}