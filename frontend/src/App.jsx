import { useState } from "react";
import ScenarioSelector from "./components/ScenarioSelector";
import PurchaseForm from "./components/PurchaseForm";
import DecisionCard from "./components/DecisionCard";
import EvidencePanel from "./components/EvidencePanel";
import "./index.css";

const scenarios = {
  recommendation: {
    id: "recommendation",
    name: "Purchase Recommendation Review",
    description:
      "Review an AI-generated purchase recommendation against inventory, suppliers, budget, storage, and demand.",
    productSku: "COFFEE-001",
    recommendedQuantity: 800,
    reason:
      "Forecast indicates increased demand and additional inventory is recommended.",
  },

  supplier: {
    id: "supplier",
    name: "Supplier Cannot Fulfil Purchase",
    description:
      "Evaluate what to do when a supplier cannot provide the full requested quantity.",
    productSku: "COFFEE-001",
    recommendedQuantity: 500,
    reason:
      "Supplier capacity may be lower than the requested purchase quantity.",
  },

  demand: {
    id: "demand",
    name: "Demand / Forecast Changed",
    description:
      "Re-evaluate purchasing when demand increases and existing inventory may no longer be sufficient.",
    productSku: "COFFEE-001",
    recommendedQuantity: 800,
    reason:
      "Recent sales increased and the forecast now requires additional inventory.",
  },

  constraint: {
    id: "constraint",
    name: "Purchasing Constraint",
    description:
      "Determine the safest action when a purchase recommendation conflicts with purchasing constraints.",
    productSku: "COFFEE-001",
    recommendedQuantity: 800,
    reason:
      "Additional inventory is required, but budget and supplier constraints must be respected.",
  },
};

function App() {
  const [selectedScenario, setSelectedScenario] =
    useState("recommendation");

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const scenario = scenarios[selectedScenario];

  const handleScenarioChange = (scenarioId) => {
    setSelectedScenario(scenarioId);
    setResult(null);
    setError("");
  };

  const handleReview = async (formData) => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const requestData = {
        ...formData,
        scenario: selectedScenario,
      };

      const response = await fetch(
        "http://localhost:8000/api/purchase/review",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify(requestData),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to review purchase"
        );
      }

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <div className="eyebrow">AI PROCUREMENT SYSTEM</div>

          <h1>AI Purchasing Agent</h1>

          <p>
            Intelligent purchase decisions with deterministic
            validation and recovery.
          </p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          Agent Online
        </div>
      </header>

      <main className="container">
        <ScenarioSelector
          scenarios={scenarios}
          selectedScenario={selectedScenario}
          onSelect={handleScenarioChange}
        />

        <section className="scenario-header">
          <div>
            <span className="section-label">
              CURRENT SCENARIO
            </span>

            <h2>{scenario.name}</h2>

            <p>{scenario.description}</p>
          </div>
        </section>

        <PurchaseForm
          scenario={scenario}
          loading={loading}
          onSubmit={handleReview}
        />

        {error && (
          <div className="error-card">
            <strong>Request failed</strong>

            <p>{error}</p>
          </div>
        )}

        {loading && (
          <div className="loading-card">
            <div className="spinner"></div>

            <div>
              <strong>
                Agent is reviewing the purchase...
              </strong>

              <p>
                Investigating inventory, suppliers, demand,
                purchase orders and constraints.
              </p>
            </div>
          </div>
        )}

        {result && !loading && (
          <div className="results">
            <div className="results-heading">
              <div>
                <span className="section-label">
                  AGENT RESULT
                </span>

                <h2>Purchase Review Complete</h2>
              </div>

              <div
                className={`decision-badge ${
                  result.decision?.decision?.toLowerCase() || ""
                }`}
              >
                {result.decision?.decision}
              </div>
            </div>

            <div className="result-grid">
              <DecisionCard result={result} />

              <EvidencePanel result={result} />
            </div>
          </div>
        )}
      </main>

      <footer>
        AI Purchasing Agent · FastAPI · LangGraph · Groq
      </footer>
    </div>
  );
}

export default App;