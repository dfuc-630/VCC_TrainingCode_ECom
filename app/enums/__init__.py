from enum import Enum


class UserRole(str, Enum):
    CUSTOMER = "customer"
    SELLER = "seller"
    ADMIN = "admin"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    CONFIRMED = "confirmed"
    SHIPPING = "shipping"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    REFUNDED = "refunded"


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    PAYMENT = "payment"
    REFUND = "refund"
    REVENUE = "revenue"
    WITHDRAW = "withdraw"
class OrderItemStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    REFUNDED = "refunded"
    COMPLETED = "completed"
    RESERVED = "reserved"
    FAILED = "failed"
    REFUND_REQUESTED = "refund_requested"
