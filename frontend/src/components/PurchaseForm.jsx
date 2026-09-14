import { useState } from "react";

export default function PurchaseForm({
  scenario,
  loading,
  onSubmit,
}) {
  const [formData, setFormData] = useState({
    product_sku: scenario.productSku,
    recommended_quantity: scenario.recommendedQuantity,
    reason: scenario.reason,
  });

  const handleChange = (field, value) => {
    setFormData((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const handleSubmit = () => {
    onSubmit({
      product_sku: formData.product_sku,
      recommended_quantity: Number(
        formData.recommended_quantity
      ),
      reason: formData.reason,
    });
  };

  return (
    <section className="purchase-form">
      <div className="section-heading">
        <span>01</span>

        <div>
          <h2>Review Recommendation</h2>
          <p>
            Enter the purchasing recommendation you want the
            agent to evaluate.
          </p>
        </div>
      </div>

      <div className="form-grid">
        <div className="form-field">
          <label>Product SKU</label>

          <input
            type="text"
            value={formData.product_sku}
            onChange={(event) =>
              handleChange(
                "product_sku",
                event.target.value
              )
            }
            placeholder="e.g. COFFEE-001"
          />
        </div>

        <div className="form-field">
          <label>Recommended Quantity</label>

          <input
            type="number"
            min="1"
            value={formData.recommended_quantity}
            onChange={(event) =>
              handleChange(
                "recommended_quantity",
                event.target.value
              )
            }
            placeholder="e.g. 800"
          />
        </div>

        <div className="form-field full-width">
          <label>Recommendation Reason</label>

          <textarea
            value={formData.reason}
            onChange={(event) =>
              handleChange(
                "reason",
                event.target.value
              )
            }
            placeholder="Why was this quantity recommended?"
            rows="4"
          />
        </div>
      </div>

      <button
        className="submit-button"
        onClick={handleSubmit}
        disabled={loading}
      >
        {loading
          ? "Agent is analyzing..."
          : "Review Purchase Recommendation →"}
      </button>
    </section>
  );
}