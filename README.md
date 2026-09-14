# AI Purchasing Agent

An AI-powered purchasing decision system that evaluates purchase recommendations against real-world procurement constraints, validates proposed actions deterministically, recovers from failed actions, and executes feasible purchase orders.

Built with **FastAPI, LangGraph, Groq, SQLAlchemy, SQLite, and React**.

---

## Overview

Retail and quick-commerce businesses frequently need to decide:

* How much inventory to purchase
* Whether an AI-generated purchase recommendation is feasible
* Which supplier should fulfill the purchase
* Whether budget, storage, supplier capacity, and MOQ constraints are satisfied
* What to do when the initial purchasing action fails
* Whether a partial purchase is better than rejecting the recommendation entirely

This project implements an AI Purchasing Agent that combines:

1. **LLM-based decision making**
2. **Deterministic business-rule validation**
3. **Recovery from failed actions**
4. **Revalidation before execution**
5. **Purchase-order execution**
6. **Evidence and reasoning returned to the user**

The system is intentionally scoped as a working prototype using mocked/seeded procurement data rather than production infrastructure.

---

## Key Scenario Demonstrated

The primary end-to-end scenario implemented and demonstrated is:

### Purchase Recommendation Review

The system receives an AI-generated recommendation to purchase **800 units** of a product.

The agent investigates:

* Current inventory
* Incoming purchase orders
* Required demand
* Supplier availability
* Supplier MOQ
* Supplier price
* Storage capacity
* Purchasing budget

The agent determines that the actual additional requirement is **600 units**.

It then attempts to purchase 600 units.

However:

```text
600 units × ₹10/unit = ₹6,000
Available budget = ₹5,000
```

The proposed action fails deterministic validation.

Instead of blindly executing or rejecting the purchase, the agent enters a recovery step and determines that the largest feasible purchase is:

```text
500 units × ₹10/unit = ₹5,000
```

The recovered action is validated again and successfully executed.

Final result:

```text
Original recommendation: 800 units
Required additional:      600 units
Recovered purchase:       500 units
Remaining shortfall:      100 units
Final cost:               ₹5,000
Purchase order:           Created
```

This demonstrates the required behavior of handling an outcome that differs from the initial expectation and recovering from a failed action.

---

## Features

### AI-Powered Decision Making

The agent uses a Groq-hosted LLM to analyze purchasing context and produce a structured purchasing decision.

The model considers:

* Inventory position
* Demand requirements
* Existing purchase orders
* Supplier options
* Budget
* Storage
* Supplier capacity
* MOQ constraints

### Deterministic Validation

The LLM does not directly control purchasing execution.

Every proposed purchase is validated using deterministic business rules before execution.

Validation checks include:

* Minimum order quantity
* Supplier capacity
* Storage capacity
* Available budget

### Recovery

If the initial proposed purchase fails validation, the agent searches for a feasible alternative.

The recovery logic considers:

* Supplier availability
* MOQ
* Budget
* Storage
* Required quantity
* Unit price

The system selects the best feasible purchase and then validates it again.

### Revalidation Before Execution

A recovered purchase is never executed immediately.

The recovered action goes through validation again before a purchase order is created.

### Purchase Order Execution

Once all constraints pass, the system creates an actual purchase order record in the SQLite database.

### Explainability

The frontend exposes:

* AI decision
* Recommended quantity
* Selected supplier
* Required additional inventory
* Original recommendation
* Reasoning
* Risk / remaining shortfall
* Validation results
* Recovery information
* Execution result

---

# Architecture

```text
                    ┌─────────────────────┐
                    │      React UI       │
                    │    localhost:5173   │
                    └──────────┬──────────┘
                               │
                               │ HTTP
                               ▼
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │    localhost:8000   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    LangGraph Agent  │
                    │                     │
                    │  Investigate        │
                    │       ↓             │
                    │  Analyze            │
                    │       ↓             │
                    │  Decide             │
                    │       ↓             │
                    │  Validate           │
                    │       ↓             │
                    │  Recover if needed  │
                    │       ↓             │
                    │  Revalidate         │
                    │       ↓             │
                    │  Execute            │
                    │       ↓             │
                    │  Finalize           │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼─────────────────┐
              │                │                 │
              ▼                ▼                 ▼
       ┌────────────┐   ┌─────────────┐   ┌─────────────┐
       │  SQLite DB │   │ Groq LLM    │   │ Deterministic│
       │            │   │             │   │ Validation   │
       │ Inventory  │   │ Decision    │   │              │
       │ Suppliers  │   │ Reasoning   │   │ Budget       │
       │ Purchase   │   │             │   │ MOQ          │
       │ Orders     │   │             │   │ Capacity     │
       │ Budget     │   │             │   │ Storage      │
       └────────────┘   └─────────────┘   └─────────────┘
```

A more detailed architecture description is available in [`architecture.md`](architecture.md).

---

# Agent Workflow

The agent follows the following workflow:

```text
Purchase Recommendation
          │
          ▼
    Investigate Data
          │
          ├── Inventory
          ├── Existing POs
          ├── Suppliers
          └── Constraints
          │
          ▼
       Analyze Need
          │
          ▼
     AI Decision
          │
          ▼
 Deterministic Validation
          │
      ┌───┴────┐
      │        │
    PASS     FAIL
      │        │
      │        ▼
      │     Recovery
      │        │
      │        ▼
      │    Revalidation
      │        │
      └───┬────┘
          │
          ▼
       Execute
          │
          ▼
    Purchase Order
```

---

# Example End-to-End Execution

The seeded scenario contains the following data:

| Input                   |        Value |
| ----------------------- | -----------: |
| Product                 | `COFFEE-001` |
| Current inventory       |          300 |
| Existing incoming PO    |          100 |
| Required demand         |        1,000 |
| Original recommendation |          800 |
| Budget                  |       ₹5,000 |
| Supplier A capacity     |          800 |
| Supplier A MOQ          |          100 |
| Supplier A unit price   |          ₹10 |

### Step 1 — Calculate Additional Requirement

```text
Required demand = 1,000
Current inventory = 300
Incoming inventory = 100

Additional requirement
= 1,000 - (300 + 100)
= 600 units
```

### Step 2 — Evaluate Recommendation

The original recommendation is 800 units, but the actual calculated additional requirement is 600 units.

The agent therefore evaluates a purchase of 600 units.

### Step 3 — Validate

```text
Quantity: 600

MOQ:
600 >= 100
PASS

Supplier capacity:
600 <= 800
PASS

Storage:
PASS

Budget:
600 × ₹10 = ₹6,000
Available = ₹5,000
FAIL
```

The initial action cannot be executed.

### Step 4 — Recovery

The agent searches for a feasible alternative.

The largest quantity that fits within the available budget is:

```text
₹5,000 / ₹10
= 500 units
```

### Step 5 — Revalidate

```text
MOQ              PASS
Supplier capacity PASS
Storage capacity  PASS
Budget            PASS
```

### Step 6 — Execute

The system creates:

```text
Purchase Order
Quantity: 500 units
Supplier: Supplier A
Cost: ₹5,000
```

The remaining uncovered requirement is:

```text
600 - 500 = 100 units
```

The agent reports this shortfall instead of pretending that the full requirement was satisfied.

---

# Technology Stack

## Backend

* Python
* FastAPI
* LangGraph
* Groq API
* SQLAlchemy
* SQLite
* Pydantic
* Uvicorn

## Frontend

* React
* Vite
* JavaScript
* CSS

## AI

* Groq API
* Configurable Groq model through environment variables

---

# Project Structure

```text
ai-purchasing-agent/
│
├── backend/
│   ├── __init__.py
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   │
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py
│   │   │   ├── state.py
│   │   │   └── prompts.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── purchasing.py
│   │   │   ├── suppliers.py
│   │   │   ├── inventory.py
│   │   │   └── validation.py
│   │   │
│   │   └── tools/
│   │       ├── __init__.py
│   │       └── purchasing_tools.py
│   │
│   ├── seed.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ScenarioSelector.jsx
│   │   │   ├── PurchaseForm.jsx
│   │   │   ├── DecisionCard.jsx
│   │   │   └── EvidencePanel.jsx
│   │   │
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   │
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── tests/
│   └── test_agent.py
│
├── architecture.md
├── README.md
├── .env.example
└── .gitignore
```

---

# Setup

## Prerequisites

Install:

* Python 3.10+
* Node.js 18+
* npm
* A Groq API key

---

## 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd ai-purchasing-agent
```

---

# Backend Setup

## 2. Create a Python virtual environment

From the project root:

### Windows

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure environment variables

Create:

```text
backend/.env
```

using:

```text
backend/.env.example
```

Example:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
DATABASE_URL=sqlite:///./purchasing.db
```

Do not commit the real API key.

---

## 5. Seed the database

From the `backend` directory:

```powershell
python seed.py
```

This creates the local SQLite database and inserts the mock purchasing data used by the demonstration.

---

## 6. Start the backend

```powershell
uvicorn app.main:app --reload
```

The backend will run at:

```text
http://localhost:8000
```

FastAPI documentation is available at:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy"
}
```

---

# Frontend Setup

Open another terminal.

From the project root:

```powershell
cd frontend
npm install
npm run dev
```

The frontend will run at:

```text
http://localhost:5173
```

Open that URL in your browser.

---

# Running the Demonstration

1. Start the backend.
2. Start the frontend.
3. Open `http://localhost:5173`.
4. Select **Purchase Recommendation Review**.
5. Keep the default recommendation of **800 units**.
6. Click **Review Purchase Recommendation**.
7. Observe the agent's investigation, decision, validation, recovery, and execution result.

Expected behavior:

```text
Original recommendation
        ↓
800 units

Calculated requirement
        ↓
600 units

Initial validation
        ↓
FAIL — budget exceeded

Recovery
        ↓
500 units

Revalidation
        ↓
PASS

Execution
        ↓
Purchase Order Created
```

---

# Resetting the Demo Database

The SQLite database is persistent.

Every successful purchase execution creates a purchase-order record. Therefore, repeated demonstrations will modify the database state.

To reset the demo:

```powershell
cd backend
Remove-Item purchasing.db
python seed.py
```

Then restart the backend:

```powershell
uvicorn app.main:app --reload
```

This restores the seeded demonstration state.

---

# API

## Health Check

```http
GET /health
```

Example:

```json
{
  "status": "healthy"
}
```

---

## Review Purchase

```http
POST /api/purchase/review
```

Request:

```json
{
  "product_sku": "COFFEE-001",
  "recommended_quantity": 800,
  "reason": "Forecast indicates increased demand and additional inventory is recommended."
}
```

The endpoint returns the final agent result, including:

* Decision
* Selected supplier
* Final quantity
* Reasoning
* Risk
* Validation results
* Recovery information
* Execution result

---

# Validation Design

A core design principle of this project is:

> **The LLM recommends; deterministic business logic validates.**

The model is responsible for reasoning about the purchasing situation, but it is not trusted to enforce financial or operational constraints.

Before execution, the system checks:

### Minimum Order Quantity

```text
requested quantity >= supplier MOQ
```

### Supplier Capacity

```text
requested quantity <= supplier available quantity
```

### Storage Capacity

```text
current inventory + requested quantity
<= storage capacity
```

### Budget

```text
requested quantity × unit price
<= available budget
```

Only when all required checks pass can the purchase order be created.

---

# Recovery Design

The system explicitly handles failed purchasing actions.

If validation fails, the agent does not simply stop.

Instead, the recovery logic:

1. Identifies the failed constraints.
2. Examines available suppliers.
3. Calculates the maximum feasible quantity for each supplier.
4. Considers MOQ, supplier capacity, budget, and storage.
5. Selects a feasible alternative.
6. Revalidates the recovered action.
7. Executes only if the recovered action passes.

This prevents the system from blindly executing an infeasible AI recommendation.

---

# Why LangGraph?

LangGraph is used to represent the purchasing process as a stateful workflow.

The graph separates:

* Investigation
* Analysis
* Decision
* Validation
* Recovery
* Revalidation
* Execution
* Final result

This makes the agent workflow explicit and allows failed actions to transition into recovery rather than terminating the process.

---

# Why Groq?

Groq provides the LLM inference layer for the project.

The application uses the Groq API rather than embedding an LLM locally, keeping the prototype lightweight enough to run on a normal development machine.

The model can be configured through:

```env
GROQ_MODEL=openai/gpt-oss-20b
```

---

# Mock Data

This project intentionally uses seeded SQLite data rather than connecting to real retail systems.

The database contains mock entities representing:

* Products
* Suppliers
* Inventory
* Purchase orders
* Budget information

This keeps the prototype deterministic, reproducible, and safe to demonstrate.

In a production system, these would be replaced by integrations with:

* ERP systems
* Inventory management systems
* Supplier APIs
* Procurement systems
* Demand forecasting systems
* Financial/budgeting systems

---

# Approval and Execution Boundaries

The prototype demonstrates automated execution after deterministic validation.

In a production deployment, higher-value purchases could require human approval before execution.

For example:

```text
Low-value purchase
      ↓
Validate
      ↓
Auto-execute


High-value purchase
      ↓
Validate
      ↓
Human approval
      ↓
Execute
```

The current project keeps the approval boundary simple to stay within the scope of the assignment.

---

# Testing and Evaluation

The project includes tests covering core deterministic purchasing behavior.

The most important evaluation scenario is:

### Scenario: Budget-Constrained Recommendation

Input:

```text
Recommendation = 800
Required additional = 600
Budget = ₹5,000
Supplier price = ₹10
```

Expected behavior:

```text
600-unit action
        ↓
Budget validation fails
        ↓
Recovery
        ↓
500-unit action
        ↓
Validation passes
        ↓
Purchase order created
```

The test strategy focuses on verifying that:

* Purchasing constraints are enforced.
* Invalid purchases are rejected.
* Recovery finds a feasible alternative.
* Recovered actions are revalidated.
* Successful validated actions can create purchase orders.
* The system does not execute an invalid initial action.

Run tests with:

```powershell
pytest
```

---

# Current Scenario Coverage

The frontend includes four scenario selections:

1. **Purchase Recommendation Review**
2. **Supplier Cannot Fulfil Purchase**
3. **Demand / Forecast Changed**
4. **Purchasing Constraint**

The primary fully demonstrated end-to-end implementation is **Purchase Recommendation Review**.

The remaining scenarios provide the intended interaction surface for extending the agent workflow.

The assignment scope requires at least one scenario to be demonstrated end-to-end, so the implementation prioritizes a complete and reliable primary scenario rather than implementing unnecessary production complexity.

---

# Design Principles

### 1. Never blindly execute an LLM recommendation

Every purchase is validated deterministically.

### 2. Recover from failures

A failed action should trigger investigation and recovery when a feasible alternative exists.

### 3. Revalidate before execution

Recovered actions must pass the same deterministic checks before they can be executed.

### 4. Explain decisions

The system exposes reasoning, constraints, risks, and actions to the user.

### 5. Preserve partial feasibility

If the system cannot fulfill the entire requirement, it can execute a feasible partial purchase and explicitly report the remaining shortfall.

### 6. Keep external systems behind services/tools

Inventory, supplier, purchasing, and validation logic are separated from the agent graph so that mock implementations can later be replaced by real integrations.

---

# Security

API keys are loaded through environment variables.

Do not commit:

```text
.env
```

The repository should only contain:

```text
.env.example
```

with placeholder values.

---

# Limitations

This is a prototype and intentionally does not implement production infrastructure.

Current limitations include:

* SQLite instead of a production database
* Mock/seeded inventory and supplier data
* No real supplier API integration
* No real ERP integration
* No authentication
* No production-grade authorization
* No real payment or procurement execution
* No real-time inventory synchronization
* No production observability infrastructure
* Limited scenario-specific workflow branching

These limitations are intentional to keep the implementation focused on the core AI purchasing workflow and recovery behavior.

---

# Future Improvements

A production version could add:

* Real ERP integrations
* Real supplier APIs
* Real-time inventory synchronization
* Demand forecasting models
* Supplier reliability history
* Multi-supplier order splitting
* Human approval workflows
* Purchase-order cancellation/modification
* Audit logging
* Authentication and role-based access control
* PostgreSQL/DynamoDB
* Distributed task execution
* Observability and tracing
* Automated evaluation across multiple purchasing scenarios

---

# Conclusion

The AI Purchasing Agent demonstrates how an LLM can be combined with deterministic business logic to make purchasing decisions safely.

The key workflow is:

```text
Investigate
    ↓
Reason
    ↓
Propose
    ↓
Validate
    ↓
Recover if necessary
    ↓
Revalidate
    ↓
Execute
    ↓
Report outcome
```

The primary demonstration shows the agent handling an initially infeasible purchase, recovering to a feasible quantity, revalidating the recovered action, and successfully creating a purchase order while transparently reporting the remaining inventory shortfall.

---

## Author

**Devang Maurya**

AI Purchasing Agent · FastAPI · LangGraph · Groq · React
