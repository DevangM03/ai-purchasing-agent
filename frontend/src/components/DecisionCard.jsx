function DecisionCard({ result }) {
  const decision = result.decision;
  const analysis = result.analysis;

  // Find the actual supplier name from the supplier list
  const selectedSupplier = analysis?.supplier_options?.find(
    (supplier) =>
      supplier.supplier_id === decision.supplier_id
  );

  const supplierName =
    selectedSupplier?.supplier_name ||
    (decision.supplier_id
      ? `Supplier ${decision.supplier_id}`
      : "—");

  const scenario = result.scenario;

  // Scenario-specific decision heading
  const decisionTitle = {
    recommendation: "Recommendation Modified",
    supplier: "Alternate Supplier Selected",
    demand: "Purchase Plan Updated",
    constraint: "Recommendation Modified",
  }[scenario] || decision.decision;

  return (
    <section className="result-card">
      <div className="card-header">
        <div>
          <span className="section-label">
            AI DECISION
          </span>

          <h2>
            {decision.decision === "MODIFY"
              ? decisionTitle
              : decision.decision}
          </h2>
        </div>

        <div className="quantity-display">
          <strong>
            {decision.quantity ?? "—"}
          </strong>

          <span>units</span>
        </div>
      </div>

      <div className="decision-details">

        {/* Supplier */}
        <div className="detail">
          <span>Supplier</span>

          <strong>
            {supplierName}
          </strong>
        </div>


        {/* Recommendation Scenario */}
        {scenario === "recommendation" && (
          <>
            <div className="detail">
              <span>Required Additional</span>

              <strong>
                {analysis?.additional_required != null
                  ? `${analysis.additional_required} units`
                  : "—"}
              </strong>
            </div>

            <div className="detail">
              <span>Original Recommendation</span>

              <strong>
                {analysis?.recommendation != null
                  ? `${analysis.recommendation} units`
                  : "—"}
              </strong>
            </div>
          </>
        )}


        {/* Supplier Failure Scenario */}
        {scenario === "supplier" && (
          <>
            <div className="detail">
              <span>Uncovered Quantity</span>

              <strong>
                {analysis?.uncovered_quantity != null
                  ? `${analysis.uncovered_quantity} units`
                  : "—"}
              </strong>
            </div>

            <div className="detail">
              <span>Purchase Order Quantity</span>

              <strong>
                {analysis?.purchase_order_quantity != null
                  ? `${analysis.purchase_order_quantity} units`
                  : "—"}
              </strong>
            </div>
          </>
        )}


        {/* Demand Change Scenario */}
        {scenario === "demand" && (
          <>
            <div className="detail">
              <span>Available Supply</span>

              <strong>
                {analysis?.available_supply != null
                  ? `${analysis.available_supply} units`
                  : "—"}
              </strong>
            </div>

            <div className="detail">
              <span>Additional Required</span>

              <strong>
                {analysis?.additional_required != null
                  ? `${analysis.additional_required} units`
                  : "—"}
              </strong>
            </div>
          </>
        )}


        {/* Purchasing Constraint Scenario */}
        {scenario === "constraint" && (
          <>
            <div className="detail">
              <span>Available Budget</span>

              <strong>
                {analysis?.budget != null
                  ? `₹${analysis.budget.toLocaleString()}`
                  : "—"}
              </strong>
            </div>

            <div className="detail">
              <span>Storage Capacity</span>

              <strong>
                {analysis?.storage_capacity != null
                  ? `${analysis.storage_capacity} units`
                  : "—"}
              </strong>
            </div>
          </>
        )}

      </div>

      <div className="reasoning">
        <span className="section-label">
          REASONING
        </span>

        <p>
          {decision.reasoning}
        </p>
      </div>

      {decision.risk && (
        <div className="risk-box">
          <span>Risk</span>

          <p>
            {decision.risk}
          </p>
        </div>
      )}
    </section>
  );
}

export default DecisionCard;