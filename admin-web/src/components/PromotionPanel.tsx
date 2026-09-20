export function PromotionPanel() {
  return (
    <div className="panel promotion">
      <div className="panel-title">Promotion</div>

      <div
        style={{
          textAlign: "center",
          padding: "20px 10px",
        }}
      >
        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: "11px",
            letterSpacing: "1.5px",
            color: "var(--color-text-secondary)",
            textTransform: "uppercase",
            marginBottom: "8px",
          }}
        >
          No active promotions
        </div>

        <div
          style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: "11px",
            color: "var(--color-text-secondary)",
            opacity: 0.6,
          }}
        >
          Live promotion workflow is next
        </div>
      </div>
    </div>
  );
}
