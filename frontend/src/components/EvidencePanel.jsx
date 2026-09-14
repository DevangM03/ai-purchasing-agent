function EvidencePanel({ result }) {
  const validation = result.validation;
  const action = result.action;
  const recovery = result.recovery;

  const checks = [
    {
      name: "Minimum Order Quantity",
      passed:
        validation.checks?.minimum_order_quantity,
    },
    {
      name: "Supplier Capacity",
      passed:
        validation.checks?.supplier_capacity,
    },
    {
      name: "Storage Capacity",
      passed:
        validation.checks?.storage_capacity,
    },
    {
      name: "Budget",
      passed: validation.checks?.budget,
    },
  ];

  return (
    <section className="result-card">
      <div className="card-header">
        <div>
          <span className="section-label">
            VALIDATION & ACTION
          </span>

          <h2>
            {validation.valid
              ? "Purchase Validated"
              : "Purchase Blocked"}
          </h2>
        </div>

        <div
          className={
            validation.valid
              ? "validation-icon success"
              : "validation-icon failure"
          }
        >
          {validation.valid ? "✓" : "!"}
        </div>
      </div>

      <div className="checks">
        {checks.map((check) => (
          <div className="check-row" key={check.name}>
            <span
              className={
                check.passed
                  ? "check-icon passed"
                  : "check-icon failed"
              }
            >
              {check.passed ? "✓" : "×"}
            </span>

            <span>{check.name}</span>

            <strong>
              {check.passed ? "PASS" : "FAIL"}
            </strong>
          </div>
        ))}
      </div>

      <div className="cost-summary">
        <div>
          <span>Total Cost</span>
          <strong>
            ₹{validation.total_cost?.toLocaleString()}
          </strong>
        </div>

        <div>
          <span>Available Budget</span>
          <strong>
            ₹{validation.available_budget?.toLocaleString()}
          </strong>
        </div>
      </div>

      {recovery?.attempted && (
        <div className="recovery-box">
          <span className="section-label">
            RECOVERY
          </span>

          <p>
            Initial action failed validation. The agent
            recovered by selecting a feasible purchase
            quantity.
          </p>

          {recovery.recovered_quantity && (
            <strong>
              Recovered quantity:{" "}
              {recovery.recovered_quantity} units
            </strong>
          )}
        </div>
      )}

      <div
        className={
          action.executed
            ? "action-box success"
            : "action-box failure"
        }
      >
        <span className="section-label">
          EXECUTION
        </span>

        {action.executed ? (
          <>
            <h3>Purchase Order Created</h3>

            <p>
              PO #{action.purchase_order?.order_id} ·{" "}
              {action.purchase_order?.quantity} units
            </p>
          </>
        ) : (
          <>
            <h3>Purchase Not Executed</h3>

            <p>{action.message}</p>
          </>
        )}
      </div>
    </section>
  );
}

export default EvidencePanel;