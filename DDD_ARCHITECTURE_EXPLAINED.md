# 🏗️ DDD Architecture - Giải Thích Chi Tiết Cấu Trúc Thư Mục

## 📌 Tổng Quan

Cấu trúc DDD được chia theo **Domain** (miền kinh doanh), không phải theo **Layer** (tầng) như code cũ.

### So Sánh: Code Cũ vs Code DDD

```
┌─ CODE CŨ (Layer-based) ─────────────────┐
│                                         │
│  app/                                   │
│  ├── models/           (Entities)       │
│  │   ├── user.py                        │
│  │   ├── order.py                       │
│  │   ├── product.py                     │
│  │   └── wallet.py                      │
│  │                                      │
│  ├── services/         (Logic)          │
│  │   ├── user_service.py                │
│  │   ├── order_service.py               │
│  │   ├── product_service.py             │
│  │   └── wallet_service.py              │
│  │                                      │
│  ├── routes/           (API)            │
│  │   ├── user_routes.py                 │
│  │   ├── order_routes.py                │
│  │   ├── product_routes.py              │
│  │   └── wallet_routes.py               │
│  │                                       │
│  └── utils/            (Utilities)      │
│      ├── validators.py                  │
│      ├── helpers.py                     │
│      └── redis_stock.py                 │
└─────────────────────────────────────────┘
       ❌ CHỈ MỀN: Logic chia rác
       ❌ Business logic scatter everywhere
       ❌ Khó test, khó maintain
```

```
┌─ CODE DDD (Domain-based) ──────────────────────┐
│                                                │
│  ddd/                                          │
│  ├── shared/              (Chung cho all)      │
│  │   ├── domain/          (Base classes)       │
│  │   └── infrastructure/  (Shared patterns)    │
│  │                                             │
│  ├── user_management/     (USER DOMAIN)        │
│  │   ├── domain/          (Business logic)     │
│  │   ├── application/     (Use cases)          │
│  │   └── infrastructure/  (DB, API)            │
│  │                                             │
│  ├── order_management/    (ORDER DOMAIN)       │
│  │   ├── domain/          (Business logic)     │
│  │   ├── application/     (Use cases)          │
│  │   └── infrastructure/  (DB, API)            │
│  │                                             │
│  ├── product_catalog/     (PRODUCT DOMAIN)     │
│  ├── payment/             (PAYMENT DOMAIN)     │
│  └── notification/        (NOTIFICATION)       │
│                                                │
└────────────────────────────────────────────────┘
       ✅ ORGANIZATION: Domain cohesion
       ✅ Business logic localized
       ✅ Easy to test, maintain, extend
```

---

## 🎯 Tại Sao Chia Như Thế?

### 1️⃣ **Isolated Business Logic**
```
❌ Cũ:
   OrderService (200+ lines) chứa:
   - User validation
   - Product loading
   - Inventory reservation
   - Payment processing
   - Notification sending
   → Một service thay đổi → Toàn bộ site bị ảnh hưởng

✅ DDD:
   Order domain (riêng) chứa:
   - Order creation logic
   - Status transitions
   - Item management
   → Mỗi domain independent
   → Bug ở Order không ảnh hưởng User
```

### 2️⃣ **Team Collaboration**
```
❌ Cũ: 2 team làm việc trên cùng order_service.py
   ❌ Conflict thường xuyên
   ❌ Blame game
   
✅ DDD: Mỗi team chủ trị domain riêng
   ✅ UserManagementTeam → ddd/user_management/
   ✅ OrderManagementTeam → ddd/order_management/
   ✅ No conflicts, clear ownership
```

### 3️⃣ **Scalability**
```
❌ Cũ: App to => models/ và services/ folder to => cái gì cũng phức tạp

✅ DDD: Mỗi domain small & focused
   ✅ User domain: chỉ 1000 lines
   ✅ Order domain: chỉ 1300 lines
   ✅ Manageable size
```

### 4️⃣ **Microservices Ready**
```
❌ Cũ: Monolithic → Khó tách thành microservice

✅ DDD: Mỗi domain có thể trở thành service
   user_management/ → User Service
   order_management/ → Order Service
   payment/ → Payment Service
   Chỉ cần move folder + adjust endpoints
```

---

## 📁 Cấu Trúc Chi Tiết

### **Level 1: Domains (Top-level folders)**

```
ddd/
├── shared/              ← Shared cho tất cả domains
├── user_management/     ← Người dùng (khách hàng, người bán, admin)
├── order_management/    ← Đơn hàng & items
├── product_catalog/     ← Sản phẩm & danh mục
├── payment/             ← Ví & thanh toán
└── notification/        ← Thông báo (Telegram, Email)
```

**Mỗi domain là một "mini-ứng-dụng" độc lập** với 3 layer riêng.

---

### **Level 2: Layers (Bên trong mỗi Domain)**

Mỗi domain có 3 layer:

```
user_management/
├── domain/              ← Layer 1: BUSINESS LOGIC
├── application/         ← Layer 2: USE CASES
└── infrastructure/      ← Layer 3: PERSISTENCE & API
```

---

## 🔍 Chi Tiết Mỗi Layer

### **1️⃣ DOMAIN LAYER** (Business Logic)

**Folder**: `user_management/domain/`

```
domain/
├── entities/            ← Rich entities (User, Order)
├── value_objects/       ← Value objects (Email, Money, Role)
├── repositories/        ← Repository interfaces (contracts)
├── services/            ← Domain services (complex business rules)
├── events.py            ← Domain events (inter-domain communication)
└── exceptions.py        ← Domain-specific exceptions
```

**Mục đích**: Chứa tất cả **business logic**, không phụ thuộc vào framework

**Ví dụ: User Entity**
```python
class User(AggregateRoot):
    def verify_password(self, plain_password) -> bool:
        """Business logic: kiểm tra mật khẩu"""
        return self._password.verify(plain_password)
    
    def can_login(self) -> bool:
        """Business logic: user có thể login không?"""
        return self.is_active and not self.is_deleted
    
    def deactivate(self):
        """Business logic: vô hiệu hóa tài khoản"""
        self.is_active = False
        self.raise_domain_event(UserDeactivatedEvent(self.id))
```

**Đặc điểm**:
- ✅ Không import Flask, SQLAlchemy, Redis
- ✅ Pure Python business logic
- ✅ 100% testable without framework
- ✅ Có thể chạy độc lập

---

### **2️⃣ APPLICATION LAYER** (Use Cases & Orchestration)

**Folder**: `user_management/application/`

```
application/
├── commands/            ← Write operations (thay đổi data)
│   ├── register_user_command.py
│   └── handlers/
│       └── register_user_handler.py
├── queries/             ← Read operations (lấy data)
│   ├── get_user_queries.py
│   └── handlers/
│       └── get_user_handlers.py
├── dto/                 ← Data Transfer Objects (API responses)
│   └── user_dto.py
└── use_cases/           ← Complex orchestration (chỉ Order domain)
    └── create_order_use_case.py
```

**Mục đích**: Kết nối business logic với infrastructure

**Ví dụ: Command Handler**
```python
class RegisterUserCommandHandler:
    def __init__(self, user_repository, event_dispatcher):
        self.repository = user_repository
        self.dispatcher = event_dispatcher
    
    def execute(self, command: RegisterUserCommand):
        # 1. Validate: email chưa tồn tại?
        if self.repository.email_exists(command.email):
            raise UserAlreadyExistsError()
        
        # 2. Create: gọi domain logic
        user = User.create(
            email=command.email,
            password=command.password,
            role=command.role,
        )
        
        # 3. Persist: lưu vào DB
        self.repository.save(user)
        
        # 4. Publish: gửi event cho domains khác
        for event in user.get_uncommitted_events():
            self.dispatcher.dispatch(event)
        
        # 5. Return: trả về DTO
        return UserDTO.from_entity(user)
```

**Đặc điểm**:
- ✅ Orchestration logic (arrange các việc)
- ✅ Still framework-independent
- ✅ Depends on Repository (interface), not implementation
- ✅ Testable with fake repositories

---

### **3️⃣ INFRASTRUCTURE LAYER** (Persistence & API)

**Folder**: `user_management/infrastructure/`

```
infrastructure/
├── persistence/         ← Database layer
│   ├── sqlalchemy_user_model.py    ← ORM model (SQLAlchemy)
│   └── sqlalchemy_user_repository.py ← Repository implementation
├── api/                 ← HTTP layer
│   └── user_routes.py   ← Flask blueprints
└── services/            ← External services (Redis, Kafka)
```

**Mục đích**: Kết nối with external systems (Database, API, Kafka)

**Ví dụ: Repository Implementation**
```python
class SqlAlchemyUserRepository(UserRepository):
    """Implementation của repository interface"""
    
    def save(self, user: User) -> None:
        # Chuyển đổi domain entity → ORM model
        model = UserModel(
            id=user.id,
            email=user.email.value,      # Email VO → string
            password_hash=user._password.hashed_value,
        )
        # Lưu vào database
        db.session.add(model)
        db.session.commit()
    
    def find_by_email(self, email: Email) -> User:
        # Lấy từ database
        model = db.session.query(UserModel).filter_by(
            email=email.value
        ).first()
        # Chuyển đổi ORM model → domain entity
        return self._to_domain(model)
```

**Flask Routes**
```python
@user_bp.route('/register', methods=['POST'])
def register():
    # 1. Extract data from HTTP request
    data = request.get_json()
    
    # 2. Create command (application layer)
    command = RegisterUserCommand(
        email=data['email'],
        password=data['password'],
    )
    
    # 3. Execute via handler (application layer)
    handler = container.get('register_user_handler')
    result = handler.execute(command)
    
    # 4. Return response
    return jsonify(result.to_dict()), 201
```

**Đặc điểm**:
- ✅ Framework-dependent (Flask, SQLAlchemy)
- ✅ Concrete implementations
- ✅ DB operations
- ✅ HTTP routing
- ✅ External service integration

---

## 🔄 Luồng Hoạt Động: Từ Request Tới Database

### **Ví Dụ: User Registration**

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Request: POST /api/v1/users/register                         │
│    Payload: {"email": "user@example.com", "password": "..."}    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. INFRASTRUCTURE LAYER: Flask Route                            │
│    infrastructure/api/user_routes.py                            │
│                                                                 │
│    @user_bp.route('/register', methods=['POST'])                │
│    def register():                                              │
│        data = request.get_json()                                │
│        command = RegisterUserCommand(                           │
│            email=data['email'],                                 │
│            password=data['password'],                           │
│        )                                                        │
│        handler = container.get('register_user_handler')         │
│        result = handler.execute(command)  ──────┐               │
│        return jsonify(result.to_dict())         │               │
└─────────────────────────────────────────────────┼───────────────┘
                                                  │
                                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. APPLICATION LAYER: Command Handler                           │
│    application/commands/handlers/register_user_handler.py       │
│                                                                 │
│    class RegisterUserCommandHandler:                            │
│        def execute(self, command):                              │
│            email = Email(command.email)  # Validate             │
│            if self.repository.email_exists(email):              │
│                raise UserAlreadyExistsError()                   │
│                                                                 │
│            user = User.create(...)  ──────┐                     │
│            self.repository.save(user)     │                     │
│            for event in user.get...():    │                     │
│                self.dispatcher.dispatch() │                     │
│            return UserDTO.from_entity()   │                     │
└───────────────────────────────────────────┼─────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. DOMAIN LAYER: Rich Entity                                    │
│    domain/entities/user.py                                      │
│                                                                 │
│    class User(AggregateRoot):                                   │
│        @staticmethod                                            │
│        def create(email, password, role):                       │
│            # Validate constraints at construction               │
│            email_vo = Email(email)          # ← Validate        │
│            password_vo = Password.from_plain(password)          │
│            role_vo = Role(role)             # ← Enum safe       │
│                                                                 │
│            user = User(                                         │
│                user_id=str(uuid4()),       # Generate ID        │
│                email=email_vo,                                  │
│                password=password_vo,                            │
│                role=role_vo,                                    │
│            )                                                    │
│            user.raise_domain_event(                             │
│                UserCreatedEvent(user.id)   # For notifications  │
│            )                                                    │
│            return user                                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. INFRASTRUCTURE LAYER: Repository                             │
│    infrastructure/persistence/sqlalchemy_user_repository.py     │
│                                                                 │
│    class SqlAlchemyUserRepository:                              │
│        def save(self, user: User):                              │
│            # Convert domain → ORM                               │
│            model = UserModel(                                   │
│                id=user.id,                                      │
│                email=user.email.value,  ← Extract from VO       │
│                password_hash=user._password.hashed,             │
│                role=user.role.value,    ← Extract from VO       │
│            )                                                    │
│            db.session.add(model)                                │
│            db.session.commit()  ───────────┐                    │
└────────────────────────────────────────────┼────────────────────┘
                                             │
                                             ▼
                                    ┌─────────────────┐
                                    │   DATABASE      │
                                    │   PostgreSQL    │
                                    │   (users table) │
                                    └─────────────────┘
```

---

## 🎯 Data Flow: Từng Layer Chịu Trách Nhiệm Cái Gì?

```
┌──────────────────────────────────────────────────────────────┐
│                    REQUEST ARRIVES                           │
│            POST /api/v1/users/register                       │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ▼
    ┌───────────────────────────────────┐
    │   INFRASTRUCTURE LAYER            │
    │                                   │
    │   Responsibility:                 │
    │   - Parse HTTP request            │
    │   - Extract JSON payload          │
    │   - Create command object         │
    │   - Route to handler              │
    └────────────┬──────────────────────┘
                 │
                 ▼
    ┌───────────────────────────────────┐
    │   APPLICATION LAYER               │
    │                                   │
    │   Responsibility:                 │
    │   - Orchestrate use case          │
    │   - Call domain methods           │
    │   - Call repository               │
    │   - Dispatch events               │
    │   - Return DTOs                   │
    └────────────┬──────────────────────┘
                 │
                 ▼
    ┌───────────────────────────────────┐
    │   DOMAIN LAYER                    │
    │                                   │
    │   Responsibility:                 │
    │   - Validate business rules       │
    │   - Enforce constraints           │
    │   - Execute domain logic          │
    │   - Raise domain events           │
    │   - Maintain invariants           │
    └────────────┬──────────────────────┘
                 │
                 ▼
    ┌───────────────────────────────────┐
    │   INFRASTRUCTURE LAYER            │
    │                                   │
    │   Responsibility:                 │
    │   - Convert domain → ORM          │
    │   - Execute SQL queries           │
    │   - Persist to database           │
    │   - Return ORM results            │
    └────────────┬──────────────────────┘
                 │
                 ▼
    ┌───────────────────────────────────┐
    │   DATABASE                        │
    │   (PostgreSQL / MySQL)            │
    └────────────┬──────────────────────┘
                 │
                 ▼
    ┌───────────────────────────────────┐
    │   INFRASTRUCTURE LAYER            │
    │                                   │
    │   Responsibility:                 │
    │   - Convert ORM → domain          │
    │   - Return to handler             │
    └────────────┬──────────────────────┘
                 │
                 ▼
    ┌───────────────────────────────────┐
    │   APPLICATION LAYER               │
    │                                   │
    │   Responsibility:                 │
    │   - Convert entity → DTO          │
    │   - Return response               │
    └────────────┬──────────────────────┘
                 │
                 ▼
    ┌───────────────────────────────────┐
    │   INFRASTRUCTURE LAYER            │
    │                                   │
    │   Responsibility:                 │
    │   - Format JSON response          │
    │   - Set HTTP status code          │
    │   - Return to client              │
    └────────────┬──────────────────────┘
                 │
                 ▼
    ┌─────────────────────────────────┐
    │   RESPONSE SENT                 │
    │   HTTP 201 Created              │
    │   {"user_id": "...", ...}       │
    └─────────────────────────────────┘
```

---

## 🔀 Inter-Domain Communication

### **Vấn đề Cũ:**
```
❌ OrderService gọi trực tiếp ProductService.get_price()
❌ ProductService gọi trực tiếp InventoryService.reserve()
❌ Mỗi service biết về các service khác
❌ High coupling → thay đổi 1 service → bao nhiêu service phải adjust?
```

### **Giải Pháp DDD: Domain Events**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  User Domain                 Order Domain                   │
│  ─────────────────           ──────────────                 │
│  UserCreatedEvent ───────────┐                              │
│  UserPasswordChanged         │                              │
│  UserDeactivated             │                              │
│                              ▼                              │
│                        OrderCreatedEvent                    │
│                        OrderConfirmedEvent ───────────┐     │
│                        OrderShippedEvent              │     │
│                        OrderCompletedEvent            │     │
│                        OrderCancelledEvent            │     │
│                        OrderFailedEvent               │     │
│                                                       ▼     │
│                      Notification Domain              │     │
│                      ──────────────────               │     │
│                      Send Telegram                    │     │
│                      Send Email                       │     │
│                      (Listens to events)              │     │
│                                                       │     │
│                      Inventory/Kafka Domain           │     │
│                      ───────────────────              │     │
│                      Reserve Stock                    │     │
│                      Update Stock                     │     │
│                      Process Async                    │     │
│                      (Listens to events)              │     │
└─────────────────────────────────────────────────────────────┘
```

**Luồng:**
1. `User.create()` → `UserCreatedEvent` raised
2. Event dispatcher publishes event (Kafka, InMemory, etc.)
3. Notification domain listens → sends notification
4. Inventory domain listens → sends welcome stock

**Lợi ích:**
- ✅ Domains không biết về nhau
- ✅ Easy to add new listener (add Slack notifications → không thay đổi User domain)
- ✅ Event sourcing friendly
- ✅ Async-ready (Kafka)

---

## 🎁 Shared Layer

```
shared/
├── domain/
│   ├── base_entity.py       ← Entity, AggregateRoot class
│   ├── value_object.py      ← ValueObject base class
│   ├── exceptions.py         ← DomainException base
│   └── value_objects/
│       └── money.py         ← Money VO (reusable)
│
└── infrastructure/
    ├── repository.py        ← Repository interface
    ├── unit_of_work.py      ← UnitOfWork pattern
    └── event_dispatcher.py  ← EventDispatcher interface + Kafka/InMemory impl
```

**Tác dụng:**
- ✅ Base classes cho tất cả domains
- ✅ Patterns như Repository, UnitOfWork
- ✅ Common value objects (Money, Email)
- ✅ Event infrastructure

---

## 🌳 Full Picture: Domains & Their Purposes

```
┌─── SHARED FOUNDATION ─────────────────────────────────────┐
│                                                            │
│  Entity, AggregateRoot, ValueObject                      │
│  Repository, UnitOfWork, EventDispatcher                 │
│  Money VO, DomainEvent, DomainException                  │
│                                                            │
└────────┬───────────────────────────────────────────────────┘
         │
         ├─ user_management/          (Người dùng)
         │  ├── Domain: User entity, Email/Password/Role VOs
         │  ├── Application: Register, Login, ChangePassword
         │  └── Infrastructure: DB, Flask routes
         │
         ├─ order_management/         (Đơn hàng)
         │  ├── Domain: Order aggregate, OrderItem entity
         │  ├── Application: CreateOrder, ConfirmOrder, ShipOrder
         │  └── Infrastructure: DB, Flask routes, Inventory service
         │
         ├─ product_catalog/          (Sản phẩm)
         │  ├── Domain: Product entity
         │  ├── Application: CreateProduct, UpdatePrice
         │  └── Infrastructure: DB, Flask routes
         │
         ├─ payment/                  (Thanh toán)
         │  ├── Domain: Wallet entity, Transaction
         │  ├── Application: Deposit, Withdraw
         │  └── Infrastructure: DB, Flask routes
         │
         └─ notification/             (Thông báo - Event-driven)
            ├── Domain: NotificationEvent
            ├── Application: Telegram sender, Email sender
            └── Infrastructure: Kafka consumer, API integrations
```

---

## 💡 Lợi Ích Của Cấu Trúc Này

### **1. Testability**
```python
# Test domain logic WITHOUT framework
def test_user_can_login():
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePass123")
    user = User(
        user_id="123",
        email=email,
        password=password,
        is_active=True,
    )
    assert user.can_login() == True  # ✅ No Flask, DB needed!
```

### **2. Reusability**
```python
# Use same User entity everywhere
user = user_repository.find_by_id("123")

# In handlers
handler = RegisterUserCommandHandler(user_repository, dispatcher)
handler.execute(command)

# In queries
GetUserByEmailQueryHandler(user_repository).execute(query)

# In tests
fake_repository.save(user)
```

### **3. Maintainability**
```
Bug in User domain?
→ Look only in user_management/ folder
→ 1000 lines, not 1 million

Bug in Order domain?
→ Look only in order_management/ folder
→ 1300 lines, not 1 million
```

### **4. Scalability**
```
Small team:
→ 1 repo, all domains

Growing team:
→ Split into microservices
  user_management/ → User Service
  order_management/ → Order Service
  payment/ → Payment Service
```

---

## 🔑 Key Concepts

| Concept | Location | Purpose |
|---------|----------|---------|
| **Entity** | domain/entities/ | Object with identity, contains business logic |
| **Aggregate** | domain/entities/ | Entity that contains other entities, maintains invariants |
| **Value Object** | domain/value_objects/ | Immutable, compared by value, no identity (Email, Money) |
| **Repository** | infrastructure/persistence/ | Abstraction for persistence, save/load aggregates |
| **Use Case** | application/use_cases/ | Orchestrates complex business process |
| **Command** | application/commands/ | Represents a write operation |
| **Query** | application/queries/ | Represents a read operation |
| **Handler** | application/commands/handlers/ | Executes command/query |
| **DTO** | application/dto/ | Data Transfer Object for API responses |
| **Domain Event** | domain/events.py | Something important happened in domain |

---

## ✅ Summary

**Tại sao chia như thế?**
- Organized by business domain, not technical layer
- Keeps related code together
- Easy to understand, test, maintain

**Ý nghĩa mỗi folder:**
- `domain/`: Pure business logic, no framework deps
- `application/`: Use cases, orchestration, DTOs
- `infrastructure/`: DB, API, external services

**Tác dụng:**
- ✅ Low coupling, high cohesion
- ✅ 100% testable
- ✅ Team-friendly (clear ownership)
- ✅ Microservices-ready
- ✅ SOLID principles

**Luồng hoạt động:**
1. Request → Infrastructure (parse)
2. Infrastructure → Application (orchestrate)
3. Application → Domain (business logic)
4. Domain → Application (result)
5. Application → Infrastructure (persist)
6. Infrastructure → Database (save)
7. Return response

---

**Hiểu rõ cấu trúc này = Hiểu rõ DDD Architecture! 🚀**
