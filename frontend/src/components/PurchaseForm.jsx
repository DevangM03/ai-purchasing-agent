import { useEffect, useState } from "react";

function PurchaseForm({
  scenario,
  loading,
  onSubmit,
}) {
  const [formData, setFormData] = useState({});

  useEffect(() => {
    if (!scenario) {
      setFormData({});
      return;
    }

    switch (scenario.id) {
      case "recommendation":
        setFormData({
          product_sku: scenario.productSku,
          recommended_quantity: scenario.recommendedQuantity,
          reason: scenario.reason,
        });
        break;

      case "supplier":
        setFormData({
          product_sku: scenario.productSku,
          purchase_order_quantity: 500,
          supplier_name: "Supplier A",
          supplier_available_quantity: 250,
          reason:
            "The supplier has reported that only part of the requested purchase can currently be fulfilled.",
        });
        break;

      case "demand":
        setFormData({
          product_sku: scenario.productSku,
          previous_forecast: 1000,
          new_forecast: 1500,
          current_inventory: 300,
          existing_purchase_order: 300,
          reason:
            "Recent sales increased significantly and the current purchasing plan may no longer cover expected demand.",
        });
        break;

      case "constraint":
        setFormData({
          product_sku: scenario.productSku,
          recommended_quantity: scenario.recommendedQuantity,
          budget: 5000,
          storage_capacity: 1200,
          reason: scenario.reason,
        });
        break;

      default:
        setFormData({});
    }
  }, [scenario]);

  const handleChange = (field, value) => {
    setFormData((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const handleSubmit = () => {
    if (!scenario) {
      return;
    }

    if (scenario.id === "recommendation") {
      onSubmit({
        product_sku: formData.product_sku,
        recommended_quantity: Number(
          formData.recommended_quantity
        ),
        reason: formData.reason,
      });

      return;
    }

    if (scenario.id === "supplier") {
      onSubmit({
        product_sku: formData.product_sku,
        purchase_order_quantity: Number(
          formData.purchase_order_quantity
        ),
        supplier_name: formData.supplier_name,
        supplier_available_quantity: Number(
          formData.supplier_available_quantity
        ),
        reason: formData.reason,
      });

      return;
    }

    if (scenario.id === "demand") {
      onSubmit({
        product_sku: formData.product_sku,
        previous_forecast: Number(
          formData.previous_forecast
        ),
        new_forecast: Number(
          formData.new_forecast
        ),
        current_inventory: Number(
          formData.current_inventory
        ),
        existing_purchase_order: Number(
          formData.existing_purchase_order
        ),
        reason: formData.reason,
      });

      return;
    }

    if (scenario.id === "constraint") {
      onSubmit({
        product_sku: formData.product_sku,
        recommended_quantity: Number(
          formData.recommended_quantity
        ),
        budget: Number(formData.budget),
        storage_capacity: Number(
          formData.storage_capacity
        ),
        reason: formData.reason,
      });
    }
  };

  const renderRecommendationForm = () => (
    <>
      <div className="form-field">
        <label>Product SKU</label>

        <input
          type="text"
          value={formData.product_sku || ""}
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
          value={formData.recommended_quantity ?? ""}
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
          value={formData.reason || ""}
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
    </>
  );

  const renderSupplierForm = () => (
    <>
      <div className="form-field">
        <label>Product SKU</label>

        <input
          type="text"
          value={formData.product_sku || ""}
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
        <label>Purchase Order Quantity</label>

        <input
          type="number"
          min="1"
          value={
            formData.purchase_order_quantity ?? ""
          }
          onChange={(event) =>
            handleChange(
              "purchase_order_quantity",
              event.target.value
            )
          }
          placeholder="e.g. 500"
        />
      </div>

      <div className="form-field">
        <label>Supplier</label>

        <input
          type="text"
          value={formData.supplier_name || ""}
          onChange={(event) =>
            handleChange(
              "supplier_name",
              event.target.value
            )
          }
          placeholder="e.g. Supplier A"
        />
      </div>

      <div className="form-field">
        <label>Supplier Available Quantity</label>

        <input
          type="number"
          min="0"
          value={
            formData.supplier_available_quantity ?? ""
          }
          onChange={(event) =>
            handleChange(
              "supplier_available_quantity",
              event.target.value
            )
          }
          placeholder="e.g. 250"
        />
      </div>

      <div className="form-field full-width">
        <label>Situation</label>

        <textarea
          value={formData.reason || ""}
          onChange={(event) =>
            handleChange(
              "reason",
              event.target.value
            )
          }
          placeholder="Describe the supplier issue."
          rows="4"
        />
      </div>
    </>
  );

  const renderDemandForm = () => (
    <>
      <div className="form-field">
        <label>Product SKU</label>

        <input
          type="text"
          value={formData.product_sku || ""}
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
        <label>Previous Forecast</label>

        <input
          type="number"
          min="0"
          value={
            formData.previous_forecast ?? ""
          }
          onChange={(event) =>
            handleChange(
              "previous_forecast",
              event.target.value
            )
          }
          placeholder="e.g. 1000"
        />
      </div>

      <div className="form-field">
        <label>New Forecast</label>

        <input
          type="number"
          min="0"
          value={formData.new_forecast ?? ""}
          onChange={(event) =>
            handleChange(
              "new_forecast",
              event.target.value
            )
          }
          placeholder="e.g. 1500"
        />
      </div>

      <div className="form-field">
        <label>Current Inventory</label>

        <input
          type="number"
          min="0"
          value={
            formData.current_inventory ?? ""
          }
          onChange={(event) =>
            handleChange(
              "current_inventory",
              event.target.value
            )
          }
          placeholder="e.g. 300"
        />
      </div>

      <div className="form-field">
        <label>Existing Purchase Order</label>

        <input
          type="number"
          min="0"
          value={
            formData.existing_purchase_order ?? ""
          }
          onChange={(event) =>
            handleChange(
              "existing_purchase_order",
              event.target.value
            )
          }
          placeholder="e.g. 300"
        />
      </div>

      <div className="form-field full-width">
        <label>Situation</label>

        <textarea
          value={formData.reason || ""}
          onChange={(event) =>
            handleChange(
              "reason",
              event.target.value
            )
          }
          placeholder="Describe what changed in demand."
          rows="4"
        />
      </div>
    </>
  );

  const renderConstraintForm = () => (
    <>
      <div className="form-field">
        <label>Product SKU</label>

        <input
          type="text"
          value={formData.product_sku || ""}
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
          value={
            formData.recommended_quantity ?? ""
          }
          onChange={(event) =>
            handleChange(
              "recommended_quantity",
              event.target.value
            )
          }
          placeholder="e.g. 800"
        />
      </div>

      <div className="form-field">
        <label>Available Budget</label>

        <input
          type="number"
          min="0"
          value={formData.budget ?? ""}
          onChange={(event) =>
            handleChange(
              "budget",
              event.target.value
            )
          }
          placeholder="e.g. 5000"
        />
      </div>

      <div className="form-field">
        <label>Storage Capacity</label>

        <input
          type="number"
          min="0"
          value={
            formData.storage_capacity ?? ""
          }
          onChange={(event) =>
            handleChange(
              "storage_capacity",
              event.target.value
            )
          }
          placeholder="e.g. 1200"
        />
      </div>

      <div className="form-field full-width">
        <label>Constraint Situation</label>

        <textarea
          value={formData.reason || ""}
          onChange={(event) =>
            handleChange(
              "reason",
              event.target.value
            )
          }
          placeholder="Describe the purchasing constraint."
          rows="4"
        />
      </div>
    </>
  );

  const renderFormFields = () => {
    if (scenario?.id === "recommendation") {
      return renderRecommendationForm();
    }

    if (scenario?.id === "supplier") {
      return renderSupplierForm();
    }

    if (scenario?.id === "demand") {
      return renderDemandForm();
    }

    if (scenario?.id === "constraint") {
      return renderConstraintForm();
    }

    return null;
  };

  const getSectionNumber = () => {
    if (scenario?.id === "recommendation") {
      return "01";
    }

    if (scenario?.id === "supplier") {
      return "02";
    }

    if (scenario?.id === "demand") {
      return "03";
    }

    if (scenario?.id === "constraint") {
      return "04";
    }

    return "01";
  };

  const getFormTitle = () => {
    if (scenario?.id === "recommendation") {
      return "Review Recommendation";
    }

    if (scenario?.id === "supplier") {
      return "Review Supplier Failure";
    }

    if (scenario?.id === "demand") {
      return "Review Demand Change";
    }

    if (scenario?.id === "constraint") {
      return "Review Purchasing Constraint";
    }

    return "Review Purchase";
  };

  const getFormDescription = () => {
    if (scenario?.id === "recommendation") {
      return "Enter the purchasing recommendation you want the agent to evaluate.";
    }

    if (scenario?.id === "supplier") {
      return "Provide the purchase order and supplier availability so the agent can determine the next action.";
    }

    if (scenario?.id === "demand") {
      return "Provide the old and new demand information so the agent can determine whether purchasing needs to change.";
    }

    if (scenario?.id === "constraint") {
      return "Provide the recommendation and constraints so the agent can determine the safest feasible action.";
    }

    return "Provide the purchasing information for the agent to evaluate.";
  };

  const getButtonText = () => {
    if (loading) {
      return "Agent is analyzing...";
    }

    if (scenario?.id === "recommendation") {
      return "Review Purchase Recommendation →";
    }

    if (scenario?.id === "supplier") {
      return "Evaluate Supplier Failure →";
    }

    if (scenario?.id === "demand") {
      return "Re-evaluate Purchase Plan →";
    }

    if (scenario?.id === "constraint") {
      return "Evaluate Constraint →";
    }

    return "Run Purchasing Agent →";
  };

  return (
    <section className="purchase-form">
      <div className="section-heading">
        <span>{getSectionNumber()}</span>

        <div>
          <h2>{getFormTitle()}</h2>

          <p>{getFormDescription()}</p>
        </div>
      </div>

      <div className="form-grid">
        {renderFormFields()}
      </div>

      <button
        type="button"
        className="submit-button"
        onClick={handleSubmit}
        disabled={loading}
      >
        {getButtonText()}
      </button>
    </section>
  );
}

export default PurchaseForm;