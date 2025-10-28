"use client";

import { useEffect, useRef, useState } from "react";

export default function CreateAdModal({
  open,
  onClose,
  onOpen,
  leftOffset = 0,
  rightOffset = 0,
  onSubmit,
}: {
  open: boolean;
  onClose: () => void;
  onOpen?: () => void;
  leftOffset?: number;
  rightOffset?: number;
  onSubmit?: (args: { brand: string; desc: string; fileName: string | null; file: File | null }) => void;
}) {
  const [brand, setBrand] = useState("");
  const [desc, setDesc] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const submitDisabled = !file;

  // Track viewport for precise centering with sidebar offset
  const [viewportWidth, setViewportWidth] = useState<number>(
    typeof window !== "undefined" ? window.innerWidth : 0
  );
  const [showTab, setShowTab] = useState<boolean>(true);
  useEffect(() => {
    const onResize = () => setViewportWidth(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  // Delay showing pull-tab until slide-down completes
  useEffect(() => {
    let t: any;
    if (!open) {
      t = setTimeout(() => setShowTab(true), 350);
    } else {
      setShowTab(false);
    }
    return () => clearTimeout(t);
  }, [open]);

  return (
    <>
    <div className="pointer-events-none fixed inset-0 z-40">
      {/* Panel as bottom sheet; no global backdrop so graph stays usable */}
      <div
        className="pointer-events-auto absolute w-[720px] max-w-[92vw] rounded-2xl border border-neutral-800 bg-neutral-950/95 text-neutral-100 shadow-2xl backdrop-blur-md"
        style={{
          left: leftOffset + (viewportWidth - leftOffset - rightOffset) / 2,
          bottom: 16,
          transform: `translate(-50%, ${open ? "0%" : "calc(110% + 16px)"})`,
          transition: "transform 400ms ease, left 400ms ease",
          maxHeight: "50vh",
          overflowY: "auto",
        }}
      >
        <div className="p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-semibold">New Ad Analysis</h3>
            <button className="text-neutral-400 hover:text-white" onClick={onClose} aria-label="Close">
              ×
            </button>
          </div>

          <div className="mt-5 grid grid-cols-1 gap-4">
            <div>
              <label className="text-sm text-neutral-400">Brand Name (optional)</label>
              <input
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
                className="mt-1 w-full rounded-md border border-neutral-800 bg-neutral-900 px-3 py-2 outline-none focus:border-neutral-600"
                placeholder="e.g., ADvisor Labs"
              />
            </div>

            <div>
              <label className="text-sm text-neutral-400">Ad Description (optional)</label>
              <textarea
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                className="mt-1 w-full rounded-md border border-neutral-800 bg-neutral-900 px-3 py-2 outline-none focus:border-neutral-600"
                rows={4}
                placeholder="Short description of your creative"
              />
            </div>

            <div>
              <label className="text-sm text-neutral-400">Upload Media (required)</label>
              <div className="mt-2 flex items-center gap-3">
                <input
                  ref={inputRef}
                  type="file"
                  accept="image/*,video/*"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  className="block w-full text-sm text-neutral-300 file:mr-4 file:rounded-md file:border file:border-neutral-700 file:bg-neutral-800 file:px-3 file:py-2 file:text-neutral-200 hover:file:bg-neutral-700"
                />
              </div>
              {file && (
                <div className="mt-2 text-xs text-neutral-400">Selected: {file.name}</div>
              )}
            </div>
          </div>

          <div className="mt-6 flex items-center justify-end gap-3">
            <button
              className="rounded-md border border-neutral-700 px-4 py-2 text-neutral-200 hover:bg-neutral-800"
              onClick={() => {
                onClose();
              }}
            >
              Cancel
            </button>
            <button
              className="rounded-md bg-neutral-100 text-black px-4 py-2 disabled:opacity-50"
              disabled={submitDisabled}
              onClick={() => {
                onSubmit?.({ brand, desc, fileName: file?.name ?? null, file });
                onClose();
                // simulate analysis completion by opening the panel via a custom event
                window.dispatchEvent(new CustomEvent("advisor:openAnalysis"));
              }}
            >
              Analyze
            </button>
          </div>
        </div>
      </div>

    </div>
    {/* Pull-tab when closed (outside overlay so it's always clickable) */}
      {showTab && (
      <button
        className="fixed z-40 bottom-4 -translate-x-1/2 rounded-full bg-neutral-900/90 border border-neutral-800 px-4 py-1.5 text-sm text-neutral-200 shadow-md hover:bg-neutral-800"
        style={{
            left: leftOffset + (viewportWidth - leftOffset - rightOffset) / 2,
          transition: "left 400ms ease",
        }}
        onClick={onOpen}
        aria-label="Open create modal"
      >
        New Ad Analysis
      </button>
    )}
    </>
  );
}


