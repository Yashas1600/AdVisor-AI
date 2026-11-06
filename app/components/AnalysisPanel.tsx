"use client";

type Attention = {
  full: number; // 0..100
  partial: number; // 0..100
  ignore: number; // 0..100
};

type TimelineScene = {
  start_seconds: number;
  end_seconds: number;
  description: string;
  visual_elements: string[];
};

type TextOverlay = {
  text: string;
  timestamp_seconds: number;
};

type VideoTimeline = {
  scenes: TimelineScene[];
  hook: string;
  on_screen_text: TextOverlay[];
  transcript: string;
  brand_first_appearance: number | null;
  cta_first_appearance: number | null;
  pacing: string;
  aspect_ratio: string;
  duration_seconds: number;
};

type PersonaReaction = {
  persona_name: string;
  skip_at_seconds: number | null;
  moment: string | null;
  attention: string;
  insight: string;
};

export type AnalysisData = {
  title: string;
  impactScore: number; // 0..100
  attention: Attention;
  insights: string[]; // 2-4 bullets
  demographicInsights: { percent: number; text: string }[]; // length 3
  timeline?: VideoTimeline | null;
  personaReactions?: PersonaReaction[] | null;
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
  const timeline = data?.timeline ?? null;
  const reactions = data?.personaReactions ?? null;

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

        {/* Video Timeline */}
        {timeline && (
          <section className="mt-4 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
            <div className="flex items-center gap-2 text-sm text-neutral-400">
              <span>Video Timeline</span>
              <span className="text-xs px-1.5 py-0.5 rounded bg-neutral-700 text-neutral-300">
                {timeline.duration_seconds.toFixed(1)}s
              </span>
              <span className="text-xs px-1.5 py-0.5 rounded bg-neutral-700 text-neutral-300">
                {timeline.pacing}
              </span>
            </div>

            {/* Timeline bar with scenes */}
            <div className="mt-3">
              <div className="relative h-6 rounded-full bg-neutral-800 overflow-hidden">
                {timeline.scenes.map((scene, i) => {
                  const left = (scene.start_seconds / timeline.duration_seconds) * 100;
                  const width = ((scene.end_seconds - scene.start_seconds) / timeline.duration_seconds) * 100;
                  const colors = ["#3b82f6", "#8b5cf6", "#06b6d4", "#f59e0b", "#ef4444", "#10b981"];
                  return (
                    <div
                      key={i}
                      className="absolute top-0 h-full opacity-60 hover:opacity-100 transition-opacity"
                      style={{
                        left: `${left}%`,
                        width: `${width}%`,
                        backgroundColor: colors[i % colors.length],
                      }}
                      title={`${scene.start_seconds.toFixed(1)}s - ${scene.end_seconds.toFixed(1)}s: ${scene.description}`}
                    />
                  );
                })}
                {/* Brand marker */}
                {timeline.brand_first_appearance != null && (
                  <div
                    className="absolute top-0 h-full w-0.5 bg-yellow-400 z-10"
                    style={{ left: `${(timeline.brand_first_appearance / timeline.duration_seconds) * 100}%` }}
                    title={`Brand appears: ${timeline.brand_first_appearance.toFixed(1)}s`}
                  />
                )}
                {/* CTA marker */}
                {timeline.cta_first_appearance != null && (
                  <div
                    className="absolute top-0 h-full w-0.5 bg-green-400 z-10"
                    style={{ left: `${(timeline.cta_first_appearance / timeline.duration_seconds) * 100}%` }}
                    title={`CTA appears: ${timeline.cta_first_appearance.toFixed(1)}s`}
                  />
                )}
                {/* Persona skip markers */}
                {reactions && reactions
                  .filter(r => r.skip_at_seconds != null)
                  .map((r, i) => (
                    <div
                      key={`skip-${i}`}
                      className="absolute top-0 h-full w-0.5 bg-red-500/50 z-10"
                      style={{ left: `${((r.skip_at_seconds ?? 0) / timeline.duration_seconds) * 100}%` }}
                      title={`${r.persona_name} skips at ${r.skip_at_seconds?.toFixed(1)}s`}
                    />
                  ))}
              </div>
              <div className="flex justify-between text-[10px] text-neutral-500 mt-1 px-0.5">
                <span>0s</span>
                <span>{(timeline.duration_seconds / 2).toFixed(0)}s</span>
                <span>{timeline.duration_seconds.toFixed(0)}s</span>
              </div>
            </div>

            {/* Hook */}
            {timeline.hook && (
              <div className="mt-3">
                <div className="text-xs text-neutral-500 mb-1">Hook (first 3-5s)</div>
                <div className="text-sm text-neutral-200 leading-relaxed">{timeline.hook}</div>
              </div>
            )}

            {/* Scene list */}
            <div className="mt-3 space-y-2">
              <div className="text-xs text-neutral-500">Scenes</div>
              {timeline.scenes.map((scene, i) => {
                const colors = ["#3b82f6", "#8b5cf6", "#06b6d4", "#f59e0b", "#ef4444", "#10b981"];
                return (
                  <div key={i} className="flex items-start gap-2 text-xs">
                    <div
                      className="mt-1 w-2 h-2 rounded-full shrink-0"
                      style={{ backgroundColor: colors[i % colors.length] }}
                    />
                    <div>
                      <span className="text-neutral-400">
                        {scene.start_seconds.toFixed(1)}s-{scene.end_seconds.toFixed(1)}s
                      </span>
                      <span className="text-neutral-200 ml-2">{scene.description}</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* On-screen text */}
            {timeline.on_screen_text.length > 0 && (
              <div className="mt-3 space-y-1">
                <div className="text-xs text-neutral-500">On-screen text</div>
                {timeline.on_screen_text.map((t, i) => (
                  <div key={i} className="text-xs flex gap-2">
                    <span className="text-neutral-400 shrink-0">{t.timestamp_seconds.toFixed(1)}s</span>
                    <span className="text-neutral-300">&ldquo;{t.text}&rdquo;</span>
                  </div>
                ))}
              </div>
            )}

            {/* Markers legend */}
            <div className="mt-3 flex gap-3 text-[10px] text-neutral-500">
              {timeline.brand_first_appearance != null && (
                <span className="flex items-center gap-1">
                  <span className="inline-block w-2 h-2 bg-yellow-400 rounded-full" /> Brand
                </span>
              )}
              {timeline.cta_first_appearance != null && (
                <span className="flex items-center gap-1">
                  <span className="inline-block w-2 h-2 bg-green-400 rounded-full" /> CTA
                </span>
              )}
              {reactions && reactions.some(r => r.skip_at_seconds != null) && (
                <span className="flex items-center gap-1">
                  <span className="inline-block w-2 h-2 bg-red-500 rounded-full" /> Skip points
                </span>
              )}
            </div>
          </section>
        )}

        {/* Persona Video Reactions */}
        {reactions && reactions.length > 0 && (
          <section className="mt-4 rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
            <div className="text-sm text-neutral-400">Persona Reactions</div>
            <div className="mt-3 space-y-3 max-h-60 overflow-y-auto">
              {reactions.map((r, i) => (
                <div key={i} className="text-xs border-l-2 pl-3 py-1" style={{
                  borderColor: r.attention === "full" ? "#1ecf62" : r.attention === "ignore" ? "#ef4444" : "#9CA3AF"
                }}>
                  <div className="font-medium text-neutral-200">{r.persona_name}</div>
                  {r.moment && (
                    <div className="text-neutral-400 mt-0.5">
                      Key moment: {r.moment}
                    </div>
                  )}
                  {r.skip_at_seconds != null && (
                    <div className="text-red-400 mt-0.5">
                      Would skip at {r.skip_at_seconds.toFixed(1)}s
                    </div>
                  )}
                  <div className="text-neutral-300 mt-0.5">{r.insight}</div>
                </div>
              ))}
            </div>
          </section>
        )}

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
