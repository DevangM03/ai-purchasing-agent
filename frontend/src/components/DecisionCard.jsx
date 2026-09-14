function DecisionCard({ result }) {
  const decision = result.decision;
  const analysis = result.analysis;

  return (
    <section className="result-card">
      <div className="card-header">
        <div>
          <span className="section-label">
            AI DECISION
          </span>

          <h2>
            {decision.decision === "MODIFY"
              ? "Recommendation Modified"
              : decision.decision}
          </h2>
        </div>

        <div className="quantity-display">
          <strong>{decision.quantity ?? "—"}</strong>
          <span>units</span>
        </div>
      </div>

      <div className="decision-details">
        <div className="detail">
          <span>Supplier</span>
          <strong>
            Supplier {decision.supplier_id ?? "—"}
          </strong>
        </div>

        <div className="detail">
          <span>Required Additional</span>
          <strong>
            {analysis.additional_required} units
          </strong>
        </div>

        <div className="detail">
          <span>Original Recommendation</span>
          <strong>
            {analysis.recommendation} units
          </strong>
        </div>
      </div>

      <div className="reasoning">
        <span className="section-label">REASONING</span>

        <p>{decision.reasoning}</p>
      </div>

      {decision.risk && (
        <div className="risk-box">
          <span>Risk</span>
          <p>{decision.risk}</p>
        </div>
      )}
    </section>
  );
}

export default DecisionCard;