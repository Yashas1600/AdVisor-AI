"use client";
import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { supabase } from "../lib/supabaseClient";
import { fetchUserAnalyses, createUserAnalysis, fetchAnalysisById } from "../lib/adAnalysis";
import { calculateFileChecksum } from "../utils/fileChecksum";

const AgentGraph = dynamic(() => import("../components/AgentGraph"), {
  ssr: false,
});
const Sidebar = dynamic(() => import("../components/Sidebar"), { ssr: false });
const CreateAdModal = dynamic(() => import("../components/CreateAdModal"), {
  ssr: false,
});
const AnalysisPanel = dynamic(() => import("../components/AnalysisPanel"), {
  ssr: false,
});
const AnalysisLoadingModal = dynamic(() => import("../components/AnalysisLoadingModal"), {
  ssr: false,
});

// Hardcoded checksum for special demo image
const DEMO_IMAGE_CHECKSUM = "e3c7678e929320af840363de9c204525362a2a35912070fceb18d934aef2bebc";

export default function DashboardPage() {
  const router = useRouter();
  const [selectedCommunity, setSelectedCommunity] = useState<number | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [createOpen, setCreateOpen] = useState<boolean>(false);
  const [analysisOpen, setAnalysisOpen] = useState<boolean>(false);
  const [loadingOpen, setLoadingOpen] = useState<boolean>(false);
  const NUM_COMMUNITIES = 20;
  const MEMBERS_PER_COMMUNITY = 50;
  type Attn = "full" | "neutral" | "ignore";
  const [analysisMap, setAnalysisMap] = useState<Record<number, { attention: Attn; insight: string }> | null>(null);
  const [panelData, setPanelData] = useState<any>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [analyses, setAnalyses] = useState<{ id: string; title: string; date: string }[]>([]);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null);
  const lastInputRef = React.useRef<{ brand: string; desc: string; fileName: string | null; file: File | null } | null>(null);

  // Check authentication
  useEffect(() => {
    const checkAuth = async () => {
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        router.push("/signin");
      } else {
        setUserEmail(data.session.user.email ?? null);
        await reloadAnalyses();
      }
    };
    checkAuth();

    const { data: sub } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!session) {
        router.push("/signin");
      } else {
        setUserEmail(session.user.email ?? null);
        reloadAnalyses();
      }
    });

    return () => {
      sub.subscription.unsubscribe();
    };
  }, [router]);

  // Analysis event handler with real API integration
  useEffect(() => {
    const handler = async () => {
      const input = lastInputRef.current;
      if (!input) return;

      try {
        // Check if this is the demo image
        let checksum = "";
        if (input.file) {
          checksum = await calculateFileChecksum(input.file);
          console.log("File checksum:", checksum);
        }

        // If demo image, show loading modal and hardcoded results
        if (checksum === DEMO_IMAGE_CHECKSUM) {
          setLoadingOpen(true);
          return; // Loading modal will handle the rest
        }
        // Step 1: Extract features if file provided
        let feature_output: any = null;
        let brandmeta_output: any = null;

        if (input?.file) {
          try {
            const form = new FormData();
            form.append("file", input.file);
            const extractRes = await fetch("/api/extract", { method: "POST", body: form });
            if (extractRes.ok) feature_output = await extractRes.json();
          } catch (_) {}

          // Step 2: Get brand metadata
          try {
            const bmPayload = feature_output
              ? {
                  features: feature_output,
                  moondream_summary: input?.desc || undefined,
                }
              : {
                  ocr_text: input?.desc || undefined,
                  detected_brand_names: input?.brand ? [input.brand] : undefined,
                };
            const bmParams = new URLSearchParams({ provider: "openai", temperature: "0.2", debug: "true" });
            const bmRes = await fetch(`/api/brandmeta?${bmParams.toString()}`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(bmPayload),
            });
            if (bmRes.ok) brandmeta_output = await bmRes.json();
          } catch (_) {}
        }

        // Step 3: Create initial analysis record in Supabase
        const title = input?.brand || input?.fileName || (input?.desc ? input.desc.slice(0, 30) : null) || "Untitled";
        const initialRecord = await createUserAnalysis({
          title,
          input: { brand: input?.brand ?? "", desc: input?.desc ?? "", fileName: input?.fileName ?? null },
          output: { panelData: null },
          feature_output,
          brandmeta_output,
          agent_results: null,
        });

        if (!initialRecord) {
          console.error("Failed to create initial analysis record");
          return;
        }

        const analysisId = initialRecord.id;

        // Step 4: Extract targeting info from brand metadata
        const targetAgeRange = brandmeta_output?.brand_meta?.audience?.age_cohort || "18-24";
        const industryKeywords = brandmeta_output?.brand_meta?.target_keywords ||
                                 [brandmeta_output?.brand_meta?.category || "fitness"];

        // Step 5: Build feature vector for ASI:One analysis
        const featureVector = feature_output || {
          moondream: {
            summary: input?.desc || "Ad creative for analysis",
            caption: "",
            cta: "",
            keywords: [],
            target_audience: targetAgeRange
          },
          features: {}
        };

        // Step 6: Call smart analysis endpoint (uses ASI:One agents)
        const analysisPayload = {
          ad_id: analysisId,
          feature_vector: featureVector,
          target_age_range: targetAgeRange,
          industry_keywords: industryKeywords,
          num_personas: 50
        };

        const analysisRes = await fetch("/api/analyze-ad-smart", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(analysisPayload),
        });

        if (!analysisRes.ok) {
          console.error("Analysis API failed:", await analysisRes.text());
          return;
        }

        const analysisData = await analysisRes.json();

        // Step 7: Map persona IDs to agent numbers (1-932)
        // First, fetch all personas to get the mapping
        const allPersonasResponse = await fetch("/api/personas");
        let personaIdToAgentNumber: Record<string, number> = {};

        if (allPersonasResponse.ok) {
          const allPersonasData = await allPersonasResponse.json();
          const allPersonas = allPersonasData.personas || [];

          // Create mapping: persona_id -> agent_number (0-based index)
          allPersonas.forEach((persona: any, index: number) => {
            personaIdToAgentNumber[persona.id] = index;
          });
        }

        // Build analysis map for graph using actual agent numbers
        const map: Record<number, { attention: Attn; insight: string }> = {};
        Object.entries(analysisData.analysis_results).forEach(([personaId, result]: [string, any]) => {
          const agentNumber = personaIdToAgentNumber[personaId];
          if (agentNumber !== undefined) {
            map[agentNumber] = {
              attention: result.attention as Attn,
              insight: result.insight
            };
          }
        });

        setAnalysisMap(map);
        console.log(`✓ Mapped ${Object.keys(map).length} personas to agent numbers for visualization`);

        // Step 8: Calculate panel data from real results
        const summary = analysisData.summary;
        const impactScore = Math.round(
          (summary.attention_percentages.full * 0.8) +
          (summary.attention_percentages.partial * 0.3)
        );

        setPanelData({
          title: "Results",
          impactScore,
          attention: {
            full: summary.attention_percentages.full,
            partial: summary.attention_percentages.partial,
            ignore: summary.attention_percentages.ignore
          },
          insights: [
            `Analysis from ${summary.total_personas} relevant persona agents.`,
            "Targeting based on demographics and industry alignment.",
          ],
          demographicInsights: [
            {
              percent: summary.attention_percentages.full,
              text: "showed full attention and engagement"
            },
            {
              percent: summary.attention_percentages.partial,
              text: "had partial interest, needs refinement"
            },
            {
              percent: summary.attention_percentages.ignore,
              text: "found it not relevant to their needs"
            },
          ],
        });

        setAnalysisOpen(true);
        await reloadAnalyses();
        setSelectedAnalysisId(analysisId);

      } catch (e) {
        console.error("Analysis error:", e);
        // Fallback to showing analysis panel even on error
        setAnalysisOpen(true);
      }
    };
    window.addEventListener("advisor:openAnalysis", handler as any);
    return () => window.removeEventListener("advisor:openAnalysis", handler as any);
  }, []);

  const reloadAnalyses = async () => {
    try {
      const rows = await fetchUserAnalyses();
      setAnalyses(
        (rows ?? []).map((r) => ({
          id: r.id,
          title: r.title ?? "Untitled",
          date: new Date(r.created_at).toLocaleString(undefined, { month: "short", year: "numeric" }),
        }))
      );
    } catch (_e) {
      setAnalyses([]);
    }
  };

  const handleAnalyzeSubmit = (args: { brand: string; desc: string; fileName: string | null; file: File | null }) => {
    lastInputRef.current = args;
  };

  const handleLoadingComplete = () => {
    setLoadingOpen(false);

    // Generate hardcoded demo analysis map
    // Simulate 932 agents with diverse attention patterns
    const demoMap: Record<number, { attention: Attn; insight: string }> = {};
    for (let i = 0; i < 932; i++) {
      let attention: Attn;
      const rand = Math.random();
      if (rand < 0.46) {
        attention = "full";
      } else if (rand < 0.85) {
        attention = "neutral";
      } else {
        attention = "ignore";
      }

      demoMap[i] = {
        attention,
        insight: attention === "full"
          ? "Strong engagement with clear messaging and professional design"
          : attention === "neutral"
          ? "Moderate interest, but colors could be more vibrant"
          : "Not relevant to my community's interests"
      };
    }

    setAnalysisMap(demoMap);

    // Set hardcoded panel data
    setPanelData({
      title: "Niche Engage Analysis",
      impactScore: 71,
      attention: {
        full: 46,
        partial: 39,
        ignore: 15
      },
      insights: [
        "The ad performed fairly well, with most viewers appreciating its clean, structured design. The dark theme feels professional, but the muted colors make key elements like the score and CTA blend into the background. Stronger contrast or subtle animation around key metrics could draw focus and improve engagement.",
        "The copy is clear but slightly formal, lacking emotional pull. Adding short, action-oriented lines beneath each score would make insights feel more personal and motivating. Expanding the \"Insights\" section automatically or adding gentle visual cues when data updates would also make the experience feel more dynamic and interactive."
      ],
      demographicInsights: [
        {
          percent: 46,
          text: "Marketing professionals aged 25–40 appreciated the modern, minimalist look and professional polish"
        },
        {
          percent: 24,
          text: "Executives (40–55) viewed it as polished but too simple, wanting more detailed metrics"
        },
        {
          percent: 15,
          text: "Younger users (18–25) lost interest quickly due to static layout and lack of visual motion"
        },
        {
          percent: 15,
          text: "Other demographics found it not relevant or engaging enough"
        }
      ],
    });

    setAnalysisOpen(true);
  };

  if (!userEmail) {
    return null; // Loading state while checking auth
  }

  return (
    <div className="relative">
      <AgentGraph
        numCommunities={NUM_COMMUNITIES}
        membersPerCommunity={MEMBERS_PER_COMMUNITY}
        maxConnectionsPerNode={10}
        selectedCommunity={selectedCommunity}
        onSelectCommunity={setSelectedCommunity}
        leftOffset={sidebarCollapsed ? 0 : 300}
        rightOffset={analysisOpen ? 420 : 0}
        analysisMap={analysisMap}
      />
      <Sidebar
        numCommunities={NUM_COMMUNITIES}
        selectedCommunity={selectedCommunity}
        onSelectCommunity={setSelectedCommunity}
        onCollapsedChange={setSidebarCollapsed}
        onRequestCreate={() => setCreateOpen(true)}
        onOpenAnalysis={() => setAnalysisOpen(true)}
        analyses={analyses}
        userEmail={userEmail}
        onSignOut={async () => {
          await supabase.auth.signOut();
          router.push("/signin");
        }}
        selectedAnalysisId={selectedAnalysisId}
        onSelectAnalysis={async (id) => {
          setSelectedAnalysisId(id);
          try {
            const rec = await fetchAnalysisById(id);
            if (rec?.output?.panelData) setPanelData(rec.output.panelData);
            const storedMap = (rec as any)?.agent_results?.byId ?? (rec as any)?.agent_results ?? null;
            if (storedMap && typeof storedMap === "object") {
              setAnalysisMap(storedMap as any);
            } else {
              setAnalysisMap(null);
            }
          } catch (_e) {
            // ignore
          }
        }}
      />
      <CreateAdModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onOpen={() => setCreateOpen(true)}
        leftOffset={sidebarCollapsed ? 0 : 300}
        rightOffset={analysisOpen ? 420 : 0}
        onSubmit={handleAnalyzeSubmit}
      />
      <AnalysisPanel
        open={analysisOpen}
        onClose={() => setAnalysisOpen(false)}
        data={panelData}
      />
      <AnalysisLoadingModal
        open={loadingOpen}
        onComplete={handleLoadingComplete}
      />
    </div>
  );
}
