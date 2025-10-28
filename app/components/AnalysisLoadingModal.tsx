"use client";

import { useEffect, useState } from "react";

interface LoadingStep {
  label: string;
  duration: number; // seconds
}

const STEPS: LoadingStep[] = [
  { label: "Uploading creative asset...", duration: 20 },
  { label: "Extracting visual features...", duration: 30 },
  { label: "Analyzing messaging and copy...", duration: 25 },
  { label: "Matching to persona communities...", duration: 25 },
  { label: "Running agent simulations...", duration: 40 },
  { label: "Generating insights...", duration: 40 },
];

export default function AnalysisLoadingModal({
  open,
  onComplete,
}: {
  open: boolean;
  onComplete: () => void;
}) {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!open) {
      setCurrentStep(0);
      setProgress(0);
      return;
    }

    const totalDuration = STEPS.reduce((sum, s) => sum + s.duration, 0);
    let elapsed = 0;

    const interval = setInterval(() => {
      elapsed += 0.1;
      const newProgress = Math.min((elapsed / totalDuration) * 100, 100);
      setProgress(newProgress);

      // Calculate which step we're on
      let stepElapsed = 0;
      for (let i = 0; i < STEPS.length; i++) {
        stepElapsed += STEPS[i].duration;
        if (elapsed < stepElapsed) {
          setCurrentStep(i);
          break;
        }
      }

      // Complete when done
      if (elapsed >= totalDuration) {
        clearInterval(interval);
        setTimeout(() => {
          onComplete();
        }, 500);
      }
    }, 100);

    return () => clearInterval(interval);
  }, [open, onComplete]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="w-[480px] max-w-[90vw] rounded-2xl border border-neutral-800 bg-neutral-950 p-8 shadow-2xl">
        <h2 className="text-2xl font-semibold text-white mb-2">Analyzing Your Ad</h2>
        <p className="text-sm text-neutral-400 mb-6">
          Running multimodal analysis with 932 persona agents...
        </p>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="h-2 w-full rounded-full bg-neutral-800 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="mt-2 text-right text-xs text-neutral-500">
            {Math.round(progress)}%
          </div>
        </div>

        {/* Steps */}
        <div className="space-y-3">
          {STEPS.map((step, idx) => (
            <div
              key={idx}
              className={`flex items-center gap-3 transition-opacity duration-300 ${
                idx === currentStep
                  ? "opacity-100"
                  : idx < currentStep
                  ? "opacity-60"
                  : "opacity-30"
              }`}
            >
              {/* Status Icon */}
              <div className="flex-shrink-0">
                {idx < currentStep ? (
                  <div className="h-5 w-5 rounded-full bg-green-500/20 flex items-center justify-center">
                    <svg className="h-3 w-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                ) : idx === currentStep ? (
                  <div className="h-5 w-5 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
                ) : (
                  <div className="h-5 w-5 rounded-full border-2 border-neutral-700" />
                )}
              </div>

              {/* Step Label */}
              <span
                className={`text-sm ${
                  idx === currentStep
                    ? "text-white font-medium"
                    : idx < currentStep
                    ? "text-neutral-500"
                    : "text-neutral-600"
                }`}
              >
                {step.label}
              </span>
            </div>
          ))}
        </div>

        <div className="mt-6 text-center text-xs text-neutral-500">
          This may take up to 3 minutes
        </div>
      </div>
    </div>
  );
}
