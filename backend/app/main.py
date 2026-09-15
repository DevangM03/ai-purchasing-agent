from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.schemas import PurchaseRequest
from app.agent.graph import build_graph


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="AI Purchasing Agent",
    description="AI agent for purchasing decision automation",
    version="1.0.0",
)


# Allow the React/Vite frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/api/purchase/review")
def review_purchase(
    request: PurchaseRequest,
    db: Session = Depends(get_db)
):
    try:
        graph = build_graph(db)

        graph_input = {
            "scenario": request.scenario,
            "product_sku": request.product_sku,
            "reason": request.reason,

            # Scenario 1
            "recommended_quantity": request.recommended_quantity,

            # Scenario 2
            "purchase_order_quantity": request.purchase_order_quantity,
            "supplier_name": request.supplier_name,
            "supplier_available_quantity": (
                request.supplier_available_quantity
            ),

            # Scenario 3
            "previous_forecast": request.previous_forecast,
            "new_forecast": request.new_forecast,
            "current_inventory": request.current_inventory,
            "existing_purchase_order": (
                request.existing_purchase_order
            ),

            # Scenario 4
            "budget": request.budget,
            "storage_capacity": request.storage_capacity,
        }

        result = graph.invoke(graph_input)

        return result["final_result"]

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))