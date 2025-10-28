"use client";

type Attention = {
  full: number; // 0..100
  partial: number; // 0..100
  ignore: number; // 0..100
};

export type AnalysisData = {
  title: string;
  impactScore: number; // 0..100
  attention: Attention;
  insights: string[]; // 2-4 bullets
  demographicInsights: { percent: number; text: string }[]; // length 3
};

export default function AnalysisPanel({
  open,
  onClose,
  data,
}: {
  open: boolean;
  onClose: () => void;
  data: AnalysisData | null;
}) {
  const width = 420;
  return (
    <aside
      className="fixed top-0 right-0 h-screen bg-neutral-950/95 border-l border-neutral-800 text-neutral-100 shadow-2xl backdrop-blur-sm"
      style={{
        width,
        transform: open ? "translateX(0)" : `translateX(${width + 24}px)`,
        transition: "transform 420ms ease",
        zIndex: 45,
      }}
      aria-hidden={!open}
    >
      <div className="h-full overflow-y-auto p-5">
        <div className="flex items-start justify-between">
          <h3 className="text-lg font-semibold">{data?.title ?? "Analysis"}</h3>
          <button
            className="text-neutral-400 hover:text-white"
            aria-label="Close analysis"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        {/* Impact */}
        <section className="mt-4 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
          <div className="flex items-center gap-2 text-sm text-neutral-400">
            <span>Impact Score</span>
            <span>ℹ️</span>
          </div>
          <div className="mt-3 flex items-end justify-between">
            <div className="text-2xl font-semibold">
              {scoreLabel(data?.impactScore ?? 0)}
            </div>
            <div className="text-4xl font-semibold">{data?.impactScore ?? 0}
              <span className="text-sm text-neutral-400"> / 100</span>
            </div>
          </div>
          <div className="mt-3 h-2 rounded-full bg-neutral-800">
            <div
              className="h-2 rounded-full bg-neutral-200"
              style={{ width: `${data?.impactScore ?? 0}%` }}
            />
          </div>
        </section>

        {/* Attention */}
        <section className="mt-4 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
          <div className="flex items-center gap-2 text-sm text-neutral-400">
            <span>Attention</span>
            <span>ℹ️</span>
          </div>
          <div className="mt-3 space-y-3 text-sm">
            {renderBar("Full", (data?.attention.full ?? 0), "#1ecf62")}
            {renderBar("Partial", (data?.attention.partial ?? 0), "#9CA3AF")}
            {renderBar("Ignore", (data?.attention.ignore ?? 0), "#ef4444")}
          </div>
        </section>

        {/* Insights */}
        <section className="mt-4 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
          <div className="text-sm text-neutral-400">Insights</div>
          <ul className="mt-3 space-y-3">
            {(data?.insights ?? []).map((t, i) => (
              <li key={i} className="text-neutral-200 leading-relaxed">{t}</li>
            ))}
          </ul>
        </section>

        {/* Demographics */}
        <section className="mt-4 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
          <div className="text-sm text-neutral-400">Demographic Insights</div>
          <ul className="mt-3 space-y-3">
            {(data?.demographicInsights ?? []).map((d, i) => (
              <li key={i} className="flex items-start gap-3">
                <span className="text-green-400 min-w-[3ch]">{d.percent}%</span>
                <span className="text-neutral-200 leading-relaxed">{d.text}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </aside>
  );
}

function renderBar(label: string, pct: number, color: string) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-20 text-neutral-300">{label}</div>
      <div className="flex-1 h-2 rounded-full bg-neutral-800">
        <div className="h-2 rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <div className="w-10 text-right text-neutral-300">{Math.round(pct)}%</div>
    </div>
  );
}

function scoreLabel(score: number) {
  if (score >= 80) return "Very High";
  if (score >= 60) return "High";
  if (score >= 40) return "Medium";
  if (score >= 20) return "Low";
  return "Very Low";
}


