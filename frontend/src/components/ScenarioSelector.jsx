function ScenarioSelector({
  scenarios,
  selectedScenario,
  onSelect,
}) {
  return (
    <section className="scenario-selector">
      <div className="section-label">TEST SCENARIO</div>

      <div className="scenario-tabs">
        {Object.entries(scenarios).map(
          ([key, scenario], index) => (
            <button
              key={key}
              className={
                selectedScenario === key
                  ? "scenario-tab active"
                  : "scenario-tab"
              }
              onClick={() => onSelect(key)}
            >
              <span className="scenario-number">
                0{index + 1}
              </span>

              <span>{scenario.name}</span>
            </button>
          )
        )}
      </div>
    </section>
  );
}

export default ScenarioSelector;