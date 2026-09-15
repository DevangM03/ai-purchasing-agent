# AI Purchasing Agent

An AI-powered procurement decision system built with **React, FastAPI, LangGraph, Groq, SQLAlchemy, and SQLite**.

The system evaluates purchasing recommendations against real procurement constraints, validates proposed actions deterministically, recovers from infeasible recommendations, revalidates recovered actions, and executes valid purchase orders.

The project focuses on a complete end-to-end **Purchase Recommendation Review** workflow while also demonstrating three additional purchasing scenarios.

---

# 1. Overview

The AI Purchasing Agent is designed to help a buyer evaluate purchasing decisions rather than blindly execute a recommendation.

A recommendation can be incorrect or infeasible.

For example:

```text
Recommended purchase = 800 units
Actual additional requirement = 600 units
Available budget = ₹5,000
Supplier price = ₹10/unit
```

The agent determines that only 600 units are actually required.

It then validates the proposed purchase:

```text
600 × ₹10 = ₹6,000
```

Since the available budget is only:

```text
₹5,000
```

the initial action fails validation.

The recovery stage finds the largest feasible purchase:

```text
₹5,000 / ₹10 = 500 units
```

The recovered action is then validated again before execution.

Final result:

```text
Decision: MODIFY
Purchase: 500 units
Cost: ₹5,000
Remaining shortfall: 100 units
```

This demonstrates the core design principle:

```text
LLM Reasoning
      ↓
Deterministic Validation
      ↓
Recovery
      ↓
Revalidation
      ↓
Execution
```

---

# 2. Key Features

* LLM-based purchasing reasoning using Groq
* LangGraph stateful workflow
* Deterministic purchasing validation
* Inventory and demand analysis
* Supplier comparison
* Purchase-order investigation
* Budget validation
* Storage-capacity validation
* Supplier-capacity validation
* MOQ validation
* Recovery from invalid purchasing actions
* Revalidation of recovered actions
* SQLite-backed procurement data
* React frontend for scenario testing
* FastAPI backend
* Automated validation tests
* Four purchasing scenarios
* Explainable final decisions
* No LLM-controlled database mutation

---

# 3. Architecture

The high-level architecture is:

```text
                         USER
                           │
                           ▼
                  ┌────────────────┐
                  │  React / Vite  │
                  └───────┬────────┘
                          │
                          │ POST /api/purchase/review
                          ▼
                  ┌────────────────┐
                  │    FastAPI     │
                  └───────┬────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │          LANGGRAPH              │
        │                                 │
        │  Investigate                    │
        │       ↓                         │
        │  Analysis                       │
        │       ↓                         │
        │  Decision ←──── Groq            │
        │       ↓                         │
        │  Validation                     │
        │       ↓                         │
        │  Recovery                       │
        │       ↓                         │
        │  Revalidation                   │
        │       ↓                         │
        │  Execute                        │
        │       ↓                         │
        │  Final                          │
        └──────────────┬──────────────────┘
                       │
          ┌────────────┼─────────────┐
          │            │             │
          ▼            ▼             ▼
     Inventory     Suppliers    Purchasing
      Service       Service       Service
          │            │             │
          └────────────┼─────────────┘
                       ▼
                 ┌────────────┐
                 │  SQLite DB │
                 └────────────┘
```

For the detailed architecture, see:

```text
architecture.md
```

---

# 4. Agent Workflow

The current LangGraph implementation uses a linear sequence of nodes:

```text
Investigate
    ↓
Analysis
    ↓
Decision
    ↓
Validation
    ↓
Recovery
    ↓
Revalidation
    ↓
Execute
    ↓
Final
```

## Important implementation detail

Recovery and revalidation are explicit nodes in the current graph.

The graph does **not** currently use conditional LangGraph edges such as:

```text
Validation → Execute
Validation → Recovery
```

Instead:

```text
Validation → Recovery → Revalidation → Execute
```

The recovery node examines the validation result and determines whether recovery is necessary.

This reflects the current implementation in:

```text
backend/app/agent/graph.py
```

---

# 5. Scenarios

The frontend provides four scenarios.

## Scenario 1 — Purchase Recommendation Review

The buyer receives a recommendation to purchase 800 units.

The agent investigates:

* Current inventory
* Expected demand
* Existing purchase orders
* Supplier availability
* Supplier MOQ
* Supplier pricing
* Storage capacity
* Budget

### Seeded data

```text
Current inventory = 300
Expected daily demand = 100
Forecast period = 10 days
Required demand = 1000
Existing incoming PO = 100

Supplier A:
    MOQ = 100
    Price = ₹10
    Availability = 800
    Lead time = 3 days

Supplier B:
    MOQ = 200
    Price = ₹9.50
    Availability = 400
    Lead time = 5 days

Budget = ₹5,000
Storage capacity = 1,200
```

The actual requirement is:

```text
1000 - 300 - 100
= 600 units
```

The initial purchase would therefore be:

```text
600 × ₹10
= ₹6,000
```

Validation fails because:

```text
₹6,000 > ₹5,000
```

Recovery finds:

```text
₹5,000 / ₹10
= 500 units
```

The recovered action passes all validation checks.

### Final result

```text
Decision = MODIFY

Original recommendation = 800
Required additional = 600
Final purchase = 500
Remaining shortfall = 100
Total cost = ₹5,000
Supplier = Supplier A
```

---

# 6. Scenario 2 — Supplier Cannot Fulfil Purchase

The original purchase order requests:

```text
500 units
```

The original supplier can provide only:

```text
250 units
```

The agent determines that the remaining:

```text
500 - 250
= 250 units
```

can be sourced from another supplier.

Supplier B can provide the remaining quantity.

### Result

```text
Decision = MODIFY

Original PO = 500
Original supplier availability = 250
Alternate supplier quantity = 250
Supplier = Supplier B
Cost = ₹2,375
```

The alternate purchase is validated before execution.

---

# 7. Scenario 3 — Demand / Forecast Changed

The original forecast is:

```text
1,000 units
```

The updated forecast becomes:

```text
1,500 units
```

Existing inventory and incoming purchase orders are considered.

Seeded scenario:

```text
Current inventory = 300
Existing PO = 300
New forecast = 1,500
```

Available supply:

```text
300 + 300
= 600 units
```

Additional requirement:

```text
1,500 - 600
= 900 units
```

The agent selects a feasible supplier purchase.

### Result

```text
Decision = MODIFY

Available supply = 600
Additional required = 900
Purchase = 400
Supplier = Supplier B
Cost = ₹3,800
Remaining shortfall = 500
```

The purchase is validated before execution.

---

# 8. Scenario 4 — Purchasing Constraint

The buyer recommends:

```text
800 units
```

but the purchasing constraints limit the feasible quantity.

The scenario uses:

```text
Budget = ₹5,000
Storage capacity = 1,200
```

Supplier A:

```text
Price = ₹10/unit
Availability = 800
```

The budget allows:

```text
₹5,000 / ₹10
= 500 units
```

Therefore the feasible purchase is:

```text
500 units
```

### Result

```text
Decision = MODIFY

Original recommendation = 800
Final purchase = 500
Supplier = Supplier A
Cost = ₹5,000
Remaining shortfall = 300
```

---

# 9. Deterministic Validation

The LLM is not trusted to enforce operational or financial constraints.

Validation is implemented in:

```text
backend/app/services/validation.py
```

Four primary checks are performed.

## Minimum Order Quantity

```text
quantity >= supplier.minimum_order_quantity
```

## Supplier Capacity

```text
quantity <= supplier.available_quantity
```

## Storage Capacity

```text
current_inventory
+ incoming_quantity
+ purchase_quantity
<= storage_capacity
```

## Budget

```text
quantity × unit_price
<= available_budget
```

The final action can only execute after validation succeeds.

---

# 10. Recovery

When a proposed action fails validation, the agent attempts to find a feasible alternative.

Conceptually:

```text
Proposed Action
      ↓
Validation
      ↓
FAIL
      ↓
Recovery
      ↓
Feasible Alternative
      ↓
Revalidation
      ↓
Execution
```

The recovery logic considers:

* Required quantity
* Supplier availability
* Supplier MOQ
* Unit price
* Available budget
* Storage capacity

For each supplier, the system calculates the maximum feasible quantity.

A supplier is excluded when the feasible quantity cannot satisfy the supplier's MOQ.

---

# 11. Revalidation

Recovered actions are never trusted automatically.

For example:

```text
Initial action:

600 units

Validation:

FAIL

Recovery:

500 units

Revalidation:

PASS

Execution:

500 units
```

This ensures that recovery cannot bypass the application's purchasing constraints.

---

# 12. LLM Responsibility

Groq is used for the reasoning layer.

The LLM can:

* Interpret procurement context
* Compare purchasing options
* Determine whether a recommendation should be accepted or modified
* Explain the decision
* Identify risks

The LLM cannot directly:

* Create purchase orders
* Bypass budget validation
* Bypass MOQ
* Bypass supplier capacity
* Bypass storage constraints

The architecture therefore separates:

```text
LLM = Reasoning

Application Code = Validation

Database Service = Execution
```

---

# 13. Execution Boundary

Purchase orders are created by:

```text
backend/app/services/purchasing.py
```

The execution service performs the database mutation.

The LLM never directly writes to SQLite.

The execution flow is:

```text
LLM Decision
     ↓
Validation
     ↓
Recovery if necessary
     ↓
Revalidation
     ↓
Purchase Order Creation
```

---

# 14. Human Approval

The current prototype does not implement a separate human approval queue or approval UI.

Instead, it uses deterministic validation as the execution safety boundary.

Only actions that pass the validation workflow are executed.

For a production system, human approval could be required for:

* Purchases above a configurable monetary threshold
* High-risk suppliers
* Large deviations from recommendations
* Purchases that leave significant uncovered demand
* Actions involving unusual constraints

A future production workflow could be:

```text
Agent Decision
      ↓
Validation
      ↓
Approval Policy
      │
      ├── Low Risk → Execute
      │
      └── High Risk → Human Approval
                              ↓
                           Execute
```

---

# 15. Project Structure

```text
ai-purchasing-agent/

│
├── .vscode/
│
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── graph.py
│   │   │   ├── prompts.py
│   │   │   └── state.py
│   │   │
│   │   ├── services/
│   │   │   ├── inventory.py
│   │   │   ├── purchasing.py
│   │   │   ├── suppliers.py
│   │   │   └── validation.py
│   │   │
│   │   ├── tools/
│   │   │   └── purchasing_tools.py
│   │   │
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   │
│   ├── .env.example
│   ├── purchasing.db
│   └── seed.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DecisionCard.jsx
│   │   │   ├── EvidencePanel.jsx
│   │   │   ├── PurchaseForm.jsx
│   │   │   └── ScenarioSelector.jsx
│   │   │
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── vite.config.js
│
├── tests/
│   ├── conftest.py
│   └── test_agent.py
│
├── .gitignore
├── README.md
└── architecture.md
```

The SQLite database used by the application is:

```text
backend/purchasing.db
```

It is ignored by Git and is generated/seeded locally.

---

# 16. Technology Stack

## Frontend

* React
* Vite
* JavaScript
* CSS

## Backend

* Python
* FastAPI
* Pydantic
* SQLAlchemy
* SQLite

## Agent

* LangGraph
* Groq LLM

## Testing

* pytest

---

# 17. Setup

## Prerequisites

Install:

* Python 3.11+
* Node.js
* npm
* Git
* Groq API key

---

# 18. Clone the Repository

```bash
git clone https://github.com/DevangM03/ai-purchasing-agent.git

cd ai-purchasing-agent
```

---

# 19. Backend Setup

Create and activate a virtual environment.

### Windows

```powershell
python -m venv venv

.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r backend\requirements.txt
```

---

# 20. Environment Configuration

Create:

```text
backend/.env
```

using:

```text
backend/.env.example
```

The environment file should contain:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
DATABASE_URL=sqlite:///./backend/purchasing.db
```

The application explicitly loads environment variables from:

```text
backend/.env
```

Never commit the real `.env` file or a real API key.

If an API key is accidentally exposed, revoke it and replace it immediately.

---

# 21. Seed the Database

From the project root:

```powershell
python backend\seed.py
```

The seeded database will be located at:

```text
backend/purchasing.db
```

The seed data contains:

* One product
* Two suppliers
* One existing purchase order
* One purchasing budget

---

# 22. Start the Backend

From the project root:

```powershell
uvicorn app.main:app --reload --app-dir backend
```

The backend runs on:

```text
http://localhost:8000
```

Health check:

```text
GET /health
```

Expected response:

```json
{
  "status": "healthy"
}
```

---

# 23. Start the Frontend

Open another terminal:

```powershell
cd frontend

npm install

npm run dev
```

The frontend runs on:

```text
http://localhost:5173
```

---

# 24. Running the Demonstration

1. Start the backend.
2. Start the frontend.
3. Open:

```text
http://localhost:5173
```

4. Select a purchasing scenario.
5. Enter the required information.
6. Submit the recommendation.
7. Review:

   * Decision
   * Quantity
   * Supplier
   * Reasoning
   * Risk
   * Validation
   * Recovery
   * Execution result

---

# 25. Resetting the Database

To reset the demonstration data:

```powershell
python backend\seed.py
```

This recreates the seeded procurement state.

The primary scenario can then be run again from a clean database.

---

# 26. API

## Purchase Review

```http
POST /api/purchase/review
```

Example:

```json
{
  "scenario": "recommendation",
  "product_sku": "COFFEE-001",
  "recommended_quantity": 800,
  "reason": "Forecast indicates increased demand and additional inventory is recommended."
}
```

The endpoint returns the final agent result containing:

```text
decision
analysis
validation
recovery
action
```

---

# 27. Testing

The project includes automated tests for the deterministic purchasing validator.

Run:

```powershell
pytest
```

Current verified result:

```text
5 passed
```

The tests cover:

* Valid purchase
* MOQ failure
* Storage-capacity failure
* Budget failure
* Supplier-capacity failure

The tests intentionally focus on the deterministic safety boundary because that is the most critical component between agent reasoning and purchase execution.

---

# 28. Manual Scenario Evaluation

All four scenarios have been manually verified against the seeded database.

| Scenario                  | Result | Final Action              |
| ------------------------- | ------ | ------------------------- |
| Recommendation Review     | PASS   | 500 units from Supplier A |
| Supplier Cannot Fulfil    | PASS   | 250 units from Supplier B |
| Demand / Forecast Changed | PASS   | 400 units from Supplier B |
| Purchasing Constraint     | PASS   | 500 units from Supplier A |

### Scenario 1

```text
Decision: MODIFY

Required additional: 600
Purchase: 500
Cost: ₹5,000
Shortfall: 100
```

### Scenario 2

```text
Decision: MODIFY

Uncovered quantity: 250
Alternate supplier: Supplier B
Purchase: 250
Cost: ₹2,375
```

### Scenario 3

```text
Decision: MODIFY

Available supply: 600
Additional required: 900
Purchase: 400
Cost: ₹3,800
Shortfall: 500
```

### Scenario 4

```text
Decision: MODIFY

Recommendation: 800
Purchase: 500
Cost: ₹5,000
Shortfall: 300
```

---

# 29. Mock Procurement Data

The seeded product is:

```text
Product:
Premium Coffee Beans 1kg

SKU:
COFFEE-001

Current inventory:
300

Expected daily demand:
100

Forecast days:
10

Storage capacity:
1,200
```

### Supplier A

```text
MOQ: 100
Price: ₹10
Availability: 800
Lead time: 3 days
Reliability: 0.95
```

### Supplier B

```text
MOQ: 200
Price: ₹9.50
Availability: 400
Lead time: 5 days
Reliability: 0.87
```

### Existing Purchase Order

```text
Quantity: 100
Status: OPEN
Supplier: Supplier A
```

### Budget

```text
₹5,000
```

---

# 30. Design Principles

### LLM for reasoning

The LLM handles contextual interpretation and decision explanation.

### Deterministic validation

Financial and operational constraints are enforced in application code.

### Recovery

A failed recommendation can be adjusted rather than blindly rejected.

### Revalidation

Recovered actions are checked again before execution.

### Service isolation

Database operations are separated from the agent workflow.

### Explainability

The final response exposes decision, reasoning, validation, recovery, risk, and execution information.

### Reproducibility

Seeded SQLite data allows the workflow to be reproduced locally.

---

# 31. Current Limitations

This is a prototype focused on demonstrating the purchasing-agent workflow.

Current limitations include:

* SQLite instead of a production database
* Mock procurement data
* No authentication
* No role-based authorization
* No real supplier APIs
* No ERP integration
* No real inventory synchronization
* No dedicated human approval queue
* No distributed task execution
* No production-grade observability
* No persistent agent decision history
* Purchase-order execution does not implement full inventory, supplier-capacity, or budget consumption accounting

The current implementation intentionally prioritizes a reliable end-to-end workflow over production infrastructure.

---

# 32. Future Improvements

Potential production improvements include:

### Human approval

Introduce configurable approval thresholds.

### Supplier integrations

Connect to real supplier systems and APIs.

### ERP integration

Synchronize inventory, purchase orders, budgets, and demand data with enterprise systems.

### Production database

Replace SQLite with PostgreSQL or another production database.

### Audit logging

Persist agent decisions, validation results, recovery actions, and approvals.

### Observability

Add structured logging, metrics, tracing, and failure monitoring.

### More advanced recovery

Support:

* Split orders
* Multi-supplier purchasing
* Deferred purchasing
* Escalation
* Lead-time optimization
* Cost optimization

### Forecast integration

Connect the demand-analysis workflow to real forecasting systems.

---

# 33. Security

Never commit:

```text
backend/.env
```

or any real API key.

The repository contains:

```text
backend/.env.example
```

with placeholders only.

The actual environment file should remain local.

If an API key is accidentally exposed, it should be revoked and replaced immediately.

---

# 34. Why This Architecture?

The central design decision is to separate **reasoning from execution**.

An LLM is useful for:

```text
Context interpretation

Decision reasoning

Supplier comparison

Explanation

Risk identification
```

Deterministic application code is better suited for:

```text
Budget enforcement

MOQ enforcement

Supplier capacity

Storage limits

Database mutation
```

Therefore:

```text
             LLM
              │
              ▼
       Proposed Action
              │
              ▼
    Deterministic Validation
              │
       ┌──────┴──────┐
       │             │
      FAIL          PASS
       │             │
       ▼             │
    Recovery         │
       │             │
       ▼             │
  Revalidation       │
       │             │
       └──────┬──────┘
              ▼
          Execution
```

This prevents an invalid LLM recommendation from directly mutating procurement data.

---

# 35. Conclusion

The AI Purchasing Agent demonstrates a complete procurement decision workflow where:

```text
Investigate
    ↓
Analyze
    ↓
Reason
    ↓
Validate
    ↓
Recover
    ↓
Revalidate
    ↓
Execute
    ↓
Explain Result
```

The project demonstrates how LLM reasoning can be combined with deterministic business rules to create a safer and more explainable purchasing workflow.

The implementation intentionally focuses on a small but complete end-to-end system rather than attempting to build a full enterprise procurement platform.
