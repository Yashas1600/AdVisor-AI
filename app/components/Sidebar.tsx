"use client";

import { useEffect, useMemo, useState } from "react";

type PreviousAd = {
  id: string;
  title: string;
  date: string;
};

export default function Sidebar({
  numCommunities = 20,
  selectedCommunity,
  onSelectCommunity,
  onCollapsedChange,
  onRequestCreate,
  onOpenAnalysis,
  analyses = [],
  userEmail,
  onSignOut,
  onSelectAnalysis,
  selectedAnalysisId,
}: {
  numCommunities?: number;
  selectedCommunity: number | null;
  onSelectCommunity: (c: number | null) => void;
  onCollapsedChange?: (collapsed: boolean) => void;
  onRequestCreate?: () => void;
  onOpenAnalysis?: () => void;
  analyses?: PreviousAd[];
  userEmail?: string | null;
  onSignOut?: () => void;
  onSelectAnalysis?: (id: string) => void;
  selectedAnalysisId?: string | null;
}) {
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [openDropdown, setOpenDropdown] = useState<boolean>(false);
  const [showCollapsedButtons, setShowCollapsedButtons] = useState<boolean>(false);

  // Delay showing collapsed floating buttons until slide-out completes
  useEffect(() => {
    let timer: any;
    if (collapsed) {
      timer = setTimeout(() => setShowCollapsedButtons(true), 350);
    } else {
      setShowCollapsedButtons(false);
    }
    return () => clearTimeout(timer);
  }, [collapsed]);
  const TABLEAU_20: string[] = [
    "#4E79A7","#A0CBE8","#F28E2B","#FFBE7D","#59A14F",
    "#8CD17D","#B6992D","#F1CE63","#499894","#86BCB6",
    "#E15759","#FF9D9A","#79706E","#BAB0AC","#D37295",
    "#FABFD2","#B07AA1","#D4A6C8","#9D7660","#D7B5A6"
  ];

  const previousAds = analyses;

  return (
    <>
      {/* Expanded drawer */}
      <aside
        className="fixed left-0 top-0 h-screen w-[300px] bg-neutral-950/95 border-r border-neutral-800 text-neutral-200 flex flex-col transition-transform duration-500 ease-out"
        style={{
          backdropFilter: "blur(4px)",
          transform: collapsed ? "translateX(-100%)" : "translateX(0)",
        }}
      >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-800">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-neutral-200 text-neutral-900 font-bold flex items-center justify-center">
                A
              </div>
              <div className="flex flex-col">
                <span className="text-sm text-neutral-400">AdVisor</span>
                {userEmail && <span className="text-[11px] text-neutral-500 truncate max-w-[160px]">{userEmail}</span>}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {onSignOut && (
                <button
                  className="px-2 py-1 text-xs rounded-md border border-neutral-700 text-neutral-300 hover:bg-neutral-800"
                  onClick={onSignOut}
                  title="Sign out"
                >
                  Sign out
                </button>
              )}
              <button
                className="p-1.5 rounded-md hover:bg-neutral-800"
                aria-label="Collapse sidebar"
                onClick={() => {
                  setCollapsed(true);
                  onCollapsedChange?.(true);
                }}
              >
                {/* collapse icon */}
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M19 12H5" />
                  <path d="M12 5L5 12l7 7" />
                </svg>
              </button>
            </div>
          </div>

          <div className="p-4 space-y-5 overflow-y-auto">
            {/* Current Society */}
            <div>
              <div className="text-xs uppercase tracking-wide text-neutral-500">Current Community</div>
              <div className="relative mt-2">
                <button
                  className="w-full rounded-md bg-neutral-900 border border-neutral-800 px-3 py-2 text-sm flex items-center justify-between"
                  onClick={() => setOpenDropdown((v) => !v)}
                >
                  <span className="flex items-center gap-2">
                    <span className="inline-block w-3 h-3 rounded-full" style={{ backgroundColor: selectedCommunity === null ? "#999" : TABLEAU_20[selectedCommunity % TABLEAU_20.length] }} />
                    {selectedCommunity === null ? "All Communities" : `Community ${String(selectedCommunity + 1).padStart(2, "0")}`}
                  </span>
                  <span className="text-neutral-500">▾</span>
                </button>
                {/* Popup */}
                {openDropdown && (
                  <div
                    className="absolute z-50 mt-2 w-full rounded-xl border border-neutral-800 bg-neutral-950/95 shadow-2xl p-2 backdrop-blur-sm transition-all duration-200"
                    style={{ maxHeight: 260, overflowY: "auto" }}
                  >
                  <button
                    className={`w-full text-left px-3 py-2 hover:bg-neutral-800 flex items-center gap-2 ${selectedCommunity === null ? "text-white" : "text-neutral-300"}`}
                    onClick={() => onSelectCommunity(null)}
                  >
                    <span className="inline-block w-3 h-3 rounded-full bg-neutral-500" />
                    All Communities
                  </button>
                  {Array.from({ length: numCommunities }).map((_, i) => (
                    <button
                      key={i}
                      className={`w-full text-left px-3 py-2 hover:bg-neutral-800 flex items-center gap-2 ${selectedCommunity === i ? "text-white" : "text-neutral-300"}`}
                      onClick={() => onSelectCommunity(i)}
                    >
                      <span
                        className="inline-block w-3 h-3 rounded-full"
                        style={{ backgroundColor: TABLEAU_20[i % TABLEAU_20.length] }}
                      />
                      {`Community ${String(i + 1).padStart(2, "0")}`}
                    </button>
                  ))}
                  </div>
                )}
              </div>
            </div>

            {/* Removed Current View for now */}

            {/* New Ad Analysis */}
            <div className="pt-1">
              <div className="text-sm flex items-center justify-between">
                <span className="text-neutral-300 font-medium">Create New Ad Analysis</span>
                <button
                  className="w-6 h-6 rounded-md border border-neutral-700 text-neutral-300 hover:bg-neutral-800"
                  aria-label="Add new ad"
                  onClick={() => onRequestCreate?.()}
                >
                  <span className="inline-block leading-none">+</span>
                </button>
              </div>
            </div>

            {/* Previous ads list */}
            <div className="space-y-2">
              {previousAds.length === 0 && (
                <div className="text-xs text-neutral-500">No analyses yet. Create one below.</div>
              )}
              {previousAds.map((ad) => {
                const isSelected = selectedAnalysisId === ad.id;
                return (
                  <button
                    key={ad.id}
                    className={`w-full text-left rounded-md px-3 py-2 border transition-all ${
                      isSelected
                        ? "bg-neutral-800 border-neutral-600 ring-1 ring-neutral-500"
                        : "bg-neutral-900/60 border-neutral-800 hover:border-neutral-700 hover:bg-neutral-900/90"
                    }`}
                    onClick={() => {
                      onSelectAnalysis?.(ad.id);
                      onOpenAnalysis?.();
                    }}
                  >
                    <div className={`text-sm truncate ${isSelected ? "text-white font-medium" : "text-neutral-200"}`}>
                      {ad.title}
                    </div>
                    <div className="text-xs text-neutral-500">{ad.date}</div>
                  </button>
                );
              })}
            </div>

            <div className="mt-6 pt-4 border-t border-neutral-800 text-xs text-neutral-500">Version 0.1</div>
          </div>
      </aside>

      {/* Collapsed buttons */}
      {showCollapsedButtons && (
        <div className="fixed left-3 top-4 flex items-center gap-3">
          <button
            className="w-10 h-10 rounded-lg bg-neutral-900/90 border border-neutral-800 text-neutral-200 hover:bg-neutral-800"
            aria-label="Open sidebar"
            onClick={() => {
              setCollapsed(false);
              onCollapsedChange?.(false);
            }}
            title="Open sidebar"
          >
            {/* drawer icon */}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mx-auto">
              <rect x="3" y="4" width="18" height="16" rx="2" />
              <path d="M3 9h18" />
            </svg>
          </button>
          <button
            className="w-10 h-10 rounded-lg bg-neutral-900/90 border border-neutral-800 text-neutral-200 hover:bg-neutral-800"
            aria-label="New ad analysis"
            title="New ad analysis"
            onClick={() => onRequestCreate?.()}
          >
            +
          </button>
        </div>
      )}
    </>
  );
}


