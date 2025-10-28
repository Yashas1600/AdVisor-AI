"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import * as d3 from "d3";

type AgentNode = {
  id: number;
  x: number;
  y: number;
  community: number;
  // Real persona data fields
  persona_id?: string;
  name?: string;
  summary?: string;
  demographics?: {
    age_range?: string;
    gender?: string;
    income_level?: string;
    location?: string;
  };
  psychographics?: {
    values?: string[];
    interests?: string[];
    lifestyle?: string;
  };
  pain_points?: string[];
  motivations?: string[];
  community_name?: string;  // Original subreddit name (e.g., "r/Fitness")
  community_display_name?: string;  // Display name (e.g., "Fitness Enthusiasts")
  // Legacy fields for backwards compatibility
  gender?: string;
  ageRange?: string;
  incomeLevel?: string;
  value1?: string;
  value2?: string;
  trait?: string;
};

type Edge = {
  source: AgentNode;
  target: AgentNode;
  community: number;
};

const DEFAULT_NODE_R = 4;
const SELECTED_NODE_R = 7; // slightly larger highlight
const MUTED_NODE_R = 3;
const ANALYSIS_NODE_R = 4; // same size as default nodes
const TRANSITION_MS = 500; // longer, smoother
const DELAY_MS = 500; // shorter delay before selected nodes grow

function generateEllipseDistributedNodes(
  numNodes: number,
  width: number,
  height: number
): AgentNode[] {
  const nodes: AgentNode[] = [];
  const genders = ["Male", "Female", "Non-binary"];
  const ages = ["Gen Z", "Millennial", "Gen X", "Boomer"];
  const incomes = ["Lower", "Middle", "Upper", "High"];
  const values = [
    "Innovation",
    "Community",
    "Sustainability",
    "Growth",
    "Trust",
    "Quality",
    "Efficiency",
    "Adventure",
  ];
  const traits = [
    "Analytical",
    "Creative",
    "Pragmatic",
    "Optimistic",
    "Skeptical",
    "Detail-oriented",
    "Bold",
  ];
  const centerX = width / 2;
  const centerY = height / 2;
  const radiusX = Math.max(240, (width * 0.95) / 2);
  const radiusY = Math.max(180, (height * 0.75) / 2);

  for (let i = 0; i < numNodes; i += 1) {
    // Random polar coordinates biased toward center via sqrt of random
    const angle = Math.random() * 2 * Math.PI;
    // Uniform distribution over ellipse area: r = sqrt(U)
    const r = Math.sqrt(Math.random());
    const x = centerX + r * radiusX * Math.cos(angle) + d3.randomNormal(0, 5)();
    const y = centerY + r * radiusY * Math.sin(angle) + d3.randomNormal(0, 5)();
    const gender = genders[Math.floor(Math.random() * genders.length)];
    const ageRange = ages[Math.floor(Math.random() * ages.length)];
    const incomeLevel = incomes[Math.floor(Math.random() * incomes.length)];
    const v1 = values[Math.floor(Math.random() * values.length)];
    let v2 = values[Math.floor(Math.random() * values.length)];
    if (v2 === v1) {
      v2 = values[(values.indexOf(v1) + 1) % values.length];
    }
    const trait = traits[Math.floor(Math.random() * traits.length)];

    nodes.push({
      id: i,
      x,
      y,
      community: 0,
      gender,
      ageRange,
      incomeLevel,
      value1: v1,
      value2: v2,
      trait,
    });
  }

  return nodes;
}

function generateCommunityAssignments(
  totalNodes: number,
  numCommunities: number,
  membersPerCommunity: number
): number[] {
  const assignments = new Array<number>(totalNodes).fill(0);
  const indices = Array.from({ length: totalNodes }, (_, i) => i);
  // Fisher-Yates shuffle
  for (let i = indices.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [indices[i], indices[j]] = [indices[j], indices[i]];
  }
  let cursor = 0;
  for (let c = 0; c < numCommunities; c += 1) {
    for (let m = 0; m < membersPerCommunity; m += 1) {
      const nodeIndex = indices[cursor];
      assignments[nodeIndex] = c;
      cursor += 1;
    }
  }
  return assignments;
}

const TABLEAU_20: string[] = [
  "#4E79A7","#A0CBE8","#F28E2B","#FFBE7D","#59A14F",
  "#8CD17D","#B6992D","#F1CE63","#499894","#86BCB6",
  "#E15759","#FF9D9A","#79706E","#BAB0AC","#D37295",
  "#FABFD2","#B07AA1","#D4A6C8","#9D7660","#D7B5A6"
];

function communityColor(index: number, _total: number): string {
  return TABLEAU_20[index % TABLEAU_20.length];
}

export default function AgentGraph({
  numCommunities = 20,
  membersPerCommunity = 50,
  maxConnectionsPerNode = 20,
  selectedCommunity: controlledSelectedCommunity,
  onSelectCommunity,
  leftOffset = 0,
  rightOffset = 0,
  analysisMap,
}: {
  numCommunities?: number;
  membersPerCommunity?: number;
  maxConnectionsPerNode?: number;
  selectedCommunity?: number | null;
  onSelectCommunity?: (c: number | null) => void;
  leftOffset?: number;
  rightOffset?: number;
  analysisMap?: Record<number, { attention: "full" | "neutral" | "ignore"; insight: string }> | null;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const gRef = useRef<SVGGElement | null>(null);
  // No persistent offset required; we use per-event deltas adjusted by zoom.

  const [viewport, setViewport] = useState<{ width: number; height: number }>(
    () => {
      if (typeof window !== "undefined") {
        return { width: window.innerWidth, height: window.innerHeight };
      }
      return { width: 0, height: 0 };
    }
  );

  const [legendStart, setLegendStart] = useState<number>(0);
  const [selectedCommunityState, setSelectedCommunityState] = useState<number | null>(null);
  const selectedCommunity =
    controlledSelectedCommunity !== undefined
      ? controlledSelectedCommunity
      : selectedCommunityState;
  const setSelectedCommunity = (val: number | null) => {
    if (onSelectCommunity) onSelectCommunity(val);
    else setSelectedCommunityState(val);
  };
  const [hoverNodeId, setHoverNodeId] = useState<number | null>(null);
  const [activeNodeId, setActiveNodeId] = useState<number | null>(null);
  const [hoverPos, setHoverPos] = useState<{ x: number; y: number } | null>(
    null
  );
  const [realPersonas, setRealPersonas] = useState<any[]>([]);
  const [communityNames, setCommunityNames] = useState<string[]>([]);
  const [communityIndexMap, setCommunityIndexMap] = useState<Map<string, number>>(new Map());

  // Fetch real personas from API
  useEffect(() => {
    const fetchPersonas = async () => {
      try {
        const response = await fetch("/api/personas");
        if (response.ok) {
          const data = await response.json();
          const personas = data.personas || [];
          setRealPersonas(personas);

          // Extract unique community display names and create index mapping
          const uniqueCommunities = data.communities || [];
          setCommunityNames(uniqueCommunities);

          // Create index map (community display name -> numeric index)
          const indexMap = new Map<string, number>();
          uniqueCommunities.forEach((name: string, index: number) => {
            indexMap.set(name, index);
          });
          setCommunityIndexMap(indexMap);

          console.log(`✓ Loaded ${personas.length} real personas from database`);
          console.log(`✓ Loaded ${uniqueCommunities.length} communities:`, uniqueCommunities);
        }
      } catch (error) {
        console.error("Error fetching personas:", error);
      }
    };
    fetchPersonas();
  }, []);

  // Resize observer to keep SVG full-viewport
  useEffect(() => {
    const updateSize = () => {
      setViewport({ width: window.innerWidth, height: window.innerHeight });
    };
    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, []);

  const nodes = useMemo(() => {
    if (!viewport.width || !viewport.height) return [] as AgentNode[];

    // Use real personas if loaded, otherwise generate fake data
    const total = realPersonas.length > 0 ? realPersonas.length : numCommunities * membersPerCommunity;
    const generated = generateEllipseDistributedNodes(
      total,
      viewport.width,
      viewport.height
    );
    const assignments = generateCommunityAssignments(
      total,
      numCommunities,
      membersPerCommunity
    );

    // Map real persona data to nodes
    for (let i = 0; i < total; i += 1) {
      generated[i].id = i;

      // If we have real personas, use them
      if (realPersonas.length > 0 && i < realPersonas.length) {
        const persona = realPersonas[i];

        // Assign community index based on display name
        const communityDisplayName = persona.community_display_name;
        const communityIndex = communityIndexMap.get(communityDisplayName) ?? assignments[i];
        generated[i].community = communityIndex;

        generated[i].persona_id = persona.id;
        generated[i].name = persona.name;
        generated[i].summary = persona.summary;
        generated[i].demographics = persona.demographics;
        generated[i].psychographics = persona.psychographics;
        generated[i].pain_points = persona.pain_points;
        generated[i].motivations = persona.motivations;
        generated[i].community_name = persona.community_name;
        generated[i].community_display_name = persona.community_display_name;

        // Map to legacy fields for display
        generated[i].gender = persona.demographics?.gender || "Unknown";
        generated[i].ageRange = persona.demographics?.age_range || "Unknown";
        generated[i].incomeLevel = persona.demographics?.income_level || "Unknown";
        generated[i].value1 = persona.psychographics?.values?.[0] || "N/A";
        generated[i].value2 = persona.psychographics?.values?.[1] || "N/A";
        generated[i].trait = persona.psychographics?.lifestyle || "N/A";
      } else {
        generated[i].community = assignments[i];
      }
    }
    return generated;
  }, [
    viewport.width,
    viewport.height,
    numCommunities,
    membersPerCommunity,
    realPersonas,
    communityIndexMap,
  ]);

  const links = useMemo(() => {
    if (nodes.length === 0) return [] as Edge[];
    const byCommunity = new Map<number, AgentNode[]>();
    for (const n of nodes) {
      const arr = byCommunity.get(n.community);
      if (arr) arr.push(n);
      else byCommunity.set(n.community, [n]);
    }

    const edges: Edge[] = [];
    const seen = new Set<string>();

    byCommunity.forEach((arr, community) => {
      const size = arr.length;
      for (let i = 0; i < size; i += 1) {
        const from = arr[i];
        const maxK = Math.min(maxConnectionsPerNode, size - 1);
        const k = Math.max(1, Math.floor(Math.random() * (maxK)) + 1);

        // Create a shuffled list of candidate indices excluding self
        const candidates: number[] = [];
        for (let j = 0; j < size; j += 1) if (j !== i) candidates.push(j);
        for (let a = candidates.length - 1; a > 0; a -= 1) {
          const b = Math.floor(Math.random() * (a + 1));
          [candidates[a], candidates[b]] = [candidates[b], candidates[a]];
        }

        for (let c = 0; c < k && c < candidates.length; c += 1) {
          const j = candidates[c];
          const to = arr[j];
          const key = from.id < to.id ? `${from.id}-${to.id}` : `${to.id}-${from.id}`;
          if (seen.has(key)) continue;
          seen.add(key);
          edges.push({ source: from, target: to, community });
        }
      }
    });

    return edges;
  }, [nodes, maxConnectionsPerNode]);

  // Set up zoom behavior
  useEffect(() => {
    if (!svgRef.current || !gRef.current) return;

    const svg = d3.select(svgRef.current);
    const g = d3.select(gRef.current);

    const zoomed = (event: d3.D3ZoomEvent<Element, unknown>) => {
      g.attr("transform", event.transform.toString());
      // Hide transient UI while zooming/panning
      setHoverNodeId(null);
      setActiveNodeId(null);
    };

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.2, 8])
      .on("zoom", zoomed);

    svg.call(zoom as any);

    // Hide hover tooltip while zooming
    svg.on("wheel", () => {
      setHoverNodeId(null);
      setActiveNodeId(null);
    });
    svg.on("touchstart", () => {
      setHoverNodeId(null);
      setActiveNodeId(null);
    });

    return () => {
      svg.on("zoom", null);
    };
  }, [viewport.width, viewport.height]);

  // Render edges and nodes and drag behavior
  useEffect(() => {
    if (!gRef.current) return;
    const g = d3.select(gRef.current);

    // Ensure separate groups for layering (edges behind nodes)
    const edgesG = g
      .selectAll<SVGGElement, unknown>("g.edges")
      .data([null as unknown as unknown])
      .join("g")
      .attr("class", "edges")
      .style("pointer-events", "none");
    const nodesG = g
      .selectAll<SVGGElement, unknown>("g.nodes")
      .data([null as unknown as unknown])
      .join("g")
      .attr("class", "nodes");

    const dragBehavior = d3
      .drag<SVGCircleElement, AgentNode>()
      .on("start", function (event) {
        // Prevent zoom from also handling this gesture
        if (event.sourceEvent && (event.sourceEvent as any).stopPropagation) {
          (event.sourceEvent as any).stopPropagation();
        }
        d3.select(this).classed("grabbing", true).style("cursor", "grabbing");
      })
      .on("drag", function (event, d) {
        const svgNode = svgRef.current;
        const t = svgNode ? d3.zoomTransform(svgNode) : d3.zoomIdentity;
        // Apply pointer delta adjusted for the current zoom scale so movement
        // distance is consistent in graph coordinates and avoids any jump.
        d.x += event.dx / t.k;
        d.y += event.dy / t.k;
        d3.select(this).attr("cx", d.x).attr("cy", d.y);

        // Update connected edges
        edgesG
          .selectAll<SVGLineElement, Edge>("line.edge")
          .filter((e) => e.source === d || e.target === d)
          .attr("x1", (e) => e.source.x)
          .attr("y1", (e) => e.source.y)
          .attr("x2", (e) => e.target.x)
          .attr("y2", (e) => e.target.y);
      })
      .on("end", function () {
        d3.select(this).classed("grabbing", false).style("cursor", "grab");
      });

    // Draw edges (complete graph per community)
    const lines = edgesG
      .selectAll<SVGLineElement, Edge>("line.edge")
      .data(links, (d: any) => `${d.source.id}-${d.target.id}`);

    lines
      .join(
        (enter) =>
          enter
            .append("line")
            .attr("class", "edge")
            .attr("x1", (d) => d.source.x)
            .attr("y1", (d) => d.source.y)
            .attr("x2", (d) => d.target.x)
            .attr("y2", (d) => d.target.y)
            .attr("stroke", (d) => communityColor(d.community, numCommunities))
            .attr("stroke-opacity", 0.10)
            .attr("stroke-width", 0.4),
        (update) =>
          update
            .attr("x1", (d) => d.source.x)
            .attr("y1", (d) => d.source.y)
            .attr("x2", (d) => d.target.x)
            .attr("y2", (d) => d.target.y),
        (exit) => exit.remove()
      );

    const circles = nodesG
      .selectAll<SVGCircleElement, AgentNode>("circle.node")
      .data(nodes, (d: any) => d.id);

    circles
      .join(
        (enter) =>
          enter
            .append("circle")
            .attr("class", "node")
            .attr("r", DEFAULT_NODE_R)
            .attr("cx", (d) => d.x)
            .attr("cy", (d) => d.y)
            .attr("fill", (d) => communityColor(d.community, numCommunities))
            .attr("stroke", "#111827") // gray-900
            .attr("stroke-width", 0.2)
            .style("cursor", "grab")
            .on("mouseenter", function (evt, d) {
              setHoverNodeId(d.id);
              const svgNode = svgRef.current;
              const t = svgNode ? d3.zoomTransform(svgNode) : d3.zoomIdentity;
              const [px, py] = d3.pointer(evt as any, svgNode as any);
              setHoverPos({ x: t.invertX(px), y: t.invertY(py) });
            })
            .on("mouseleave", function () {
              setHoverNodeId(null);
              setHoverPos(null);
            })
            .on("mousemove", function (evt, d) {
              if (hoverNodeId !== d.id) return;
              const svgNode = svgRef.current;
              const t = svgNode ? d3.zoomTransform(svgNode) : d3.zoomIdentity;
              const [px, py] = d3.pointer(evt as any, svgNode as any);
              setHoverPos({ x: t.invertX(px), y: t.invertY(py) });
            })
            .on("click", function (_evt, d) {
              // Allow clicking on any node to open the detail panel
              setActiveNodeId((prev) => (prev === d.id ? null : d.id));
            }),
        (update) => update,
        (exit) => exit.remove()
      )
      .call(dragBehavior as any);

    // Initial styling based on selection
    g.selectAll<SVGCircleElement, AgentNode>("circle.node")
      .attr("fill", (d) => {
        const a = analysisMap?.[d.id];
        if (a) {
          if (a.attention === "full") return "#22c55e";
          if (a.attention === "ignore") return "#ef4444";
          return "#9CA3AF";
        }
        return selectedCommunity === null || d.community === selectedCommunity
          ? communityColor(d.community, numCommunities)
          : "#3f3f46";
      })
      .attr("opacity", (d) =>
        analysisMap
          ? analysisMap[d.id]
            ? 1
            : 0.15
          : selectedCommunity === null || d.community === selectedCommunity
          ? 1
          : 0.25
      )
      .attr("r", (d) => {
        // If there's an analysis map, analyzed nodes get bigger size
        if (analysisMap && analysisMap[d.id]) {
          return ANALYSIS_NODE_R;
        }
        return selectedCommunity === null
          ? DEFAULT_NODE_R
          : d.community === selectedCommunity
          ? SELECTED_NODE_R
          : MUTED_NODE_R;
      })
      .attr("stroke", "#111827")
      .attr("stroke-width", 0.2);

    g.selectAll<SVGLineElement, Edge>("line.edge")
      .attr("stroke", (d) =>
        selectedCommunity === null || d.community === selectedCommunity
          ? communityColor(d.community, numCommunities)
          : "#3f3f46"
      )
      .attr("stroke-opacity", (d) =>
        selectedCommunity === null || d.community === selectedCommunity
          ? 0.14
          : 0.04
      );

    return () => {
      // no-op cleanup
    };
  }, [nodes, links, selectedCommunity, numCommunities, analysisMap]);

  // Update styling when selection or analysis changes without re-binding drag
  useEffect(() => {
    if (!gRef.current) return;
    const g = d3.select(gRef.current);
    const circles = g.selectAll<SVGCircleElement, AgentNode>("circle.node");

    // Color and opacity with a longer transition
    circles
      .transition()
      .duration(TRANSITION_MS)
      .ease(d3.easeCubicOut)
      .attr("fill", (d) => {
        const a = analysisMap?.[d.id];
        if (a) {
          if (a.attention === "full") return "#22c55e";
          if (a.attention === "ignore") return "#ef4444";
          return "#9CA3AF";
        }
        return selectedCommunity === null || d.community === selectedCommunity
          ? communityColor(d.community, numCommunities)
          : "#3f3f46";
      })
      .attr("opacity", (d) =>
        analysisMap
          ? analysisMap[d.id]
            ? 1
            : 0.15
          : selectedCommunity === null || d.community === selectedCommunity
          ? 1
          : 0.25
      )
      .attr("stroke", (d) => (hoverNodeId === d.id ? "#ffffff" : "#111827"))
      .attr("stroke-width", (d) => (hoverNodeId === d.id ? 3 : 0.2));

    // Radius: selected nodes wait, then grow; others adjust immediately
    circles.each(function (d) {
      const sel = d3.select(this);

      // If node is in analysis map, make it bigger
      if (analysisMap && analysisMap[d.id]) {
        sel
          .transition()
          .duration(TRANSITION_MS)
          .ease(d3.easeCubicOut)
          .attr("r", ANALYSIS_NODE_R);
        return;
      }

      if (selectedCommunity === null) {
        sel
          .transition()
          .duration(TRANSITION_MS)
          .ease(d3.easeCubicOut)
          .attr("r", DEFAULT_NODE_R);
      } else if (d.community === selectedCommunity) {
        if (hoverNodeId !== null) return;
        sel.interrupt();
        sel.attr("r", DEFAULT_NODE_R);
        sel
          .transition()
          .delay(DELAY_MS)
          .duration(TRANSITION_MS)
          .ease(d3.easeCubicOut)
          .attr("r", SELECTED_NODE_R);
      } else {
        sel
          .transition()
          .duration(TRANSITION_MS)
          .ease(d3.easeCubicOut)
          .attr("r", MUTED_NODE_R);
      }
    });

    // Edge transitions
    g.selectAll<SVGLineElement, Edge>("line.edge")
      .transition()
      .duration(TRANSITION_MS)
      .ease(d3.easeCubicOut)
      .attr("stroke", (d) =>
        selectedCommunity === null || d.community === selectedCommunity
          ? communityColor(d.community, numCommunities)
          : "#3f3f46"
      )
      .attr("stroke-opacity", (d) =>
        selectedCommunity === null || d.community === selectedCommunity
          ? 0.14
          : 0.04
      );
  }, [selectedCommunity, numCommunities, analysisMap]);

  // Hover outline only (no radius change)
  useEffect(() => {
    if (!gRef.current) return;
    const g = d3.select(gRef.current);
    g.selectAll<SVGCircleElement, AgentNode>("circle.node")
      .transition()
      .duration(120)
      .ease(d3.easeLinear)
      .attr("stroke", (d) => (hoverNodeId === d.id ? "#ffffff" : "#111827"))
      .attr("stroke-width", (d) => (hoverNodeId === d.id ? 3 : 0.2));
  }, [hoverNodeId]);

  return (
    <div
      ref={containerRef}
      className="w-screen h-screen overflow-hidden bg-black text-white"
      style={{ touchAction: "none", position: "relative" }}
    >
      {/* Legend */}
      {(() => {
        const compact = leftOffset > 0 && rightOffset > 0;
        const buttonBase = compact
          ? "rounded-full bg-neutral-900/80 border border-neutral-700 px-2 py-0.5 text-xs"
          : "rounded-full bg-neutral-900/80 border border-neutral-700 px-2 py-1 text-sm";
        const gapClass = compact ? "gap-1.5" : "gap-2";
        const chipPadding = compact ? "px-2 py-1 text-xs" : "px-3 py-1.5 text-sm";
        const dotSize = compact ? "w-2.5 h-2.5" : "w-3 h-3";
        const chipClass = (active: boolean) =>
          `flex items-center ${gapClass} rounded-full ${chipPadding} border ` +
          (active
            ? "bg-neutral-100 text-black border-neutral-200"
            : "bg-neutral-900/80 text-white border-neutral-700");
        return (
      <div
        className="absolute top-4 -translate-x-1/2 flex items-center gap-2 max-w-[92vw]"
        style={{
          pointerEvents: "auto",
          left: leftOffset + (viewport.width - leftOffset - rightOffset) / 2,
          transition: "left 400ms ease",
        }}
      >
        <button
          className={`${buttonBase} disabled:opacity-40`}
          onClick={() => setLegendStart((s) => Math.max(0, s - 5))}
          disabled={legendStart === 0}
        >
          ‹
        </button>
        <div className={`flex items-center ${gapClass}`}>
          {Array.from({ length: 5 })
            .map((_, idx) => legendStart + idx)
            .filter((i) => i < (communityNames.length || numCommunities))
            .map((i) => {
              const active = selectedCommunity === i;
              return (
                <button
                  key={i}
                  onClick={() => setSelectedCommunity(selectedCommunity === i ? null : i)}
                  className={chipClass(active)}
                >
                  <span
                    className={`inline-block ${dotSize} rounded-full`}
                    style={{ backgroundColor: communityColor(i, numCommunities) }}
                  />
                  <span>{communityNames[i] || `Community ${String(i + 1).padStart(2, "0")}`}</span>
                </button>
              );
            })}
        </div>
        <button
          className={`${buttonBase} disabled:opacity-40`}
          onClick={() =>
            setLegendStart((s) => Math.min(Math.max(0, (communityNames.length || numCommunities) - 5), s + 5))
          }
          disabled={legendStart >= Math.max(0, (communityNames.length || numCommunities) - 5)}
        >
          ›
        </button>
      </div>
        );
      })()}

      <svg
        ref={svgRef}
        width={viewport.width}
        height={viewport.height}
        style={{ touchAction: "none" }}
      >
        <rect
          width={viewport.width}
          height={viewport.height}
          fill="transparent"
          pointerEvents="all"
        />
        <g ref={gRef} />
      </svg>

      {/* Hover tooltip (small, offset, follows pointer with transition) - hide when node is clicked */}
      {hoverNodeId !== null && activeNodeId === null && hoverPos && (() => {
        const n = nodes.find((x) => x.id === hoverNodeId);
        if (!n) return null;
        const a = analysisMap?.[n.id];

        // Estimate tooltip dimensions
        const tooltipWidth = 320; // increased width for 2 lines
        const tooltipHeight = a ? 100 : 30; // increased height for 2 lines of insight
        const padding = 16;

        // Calculate position with boundary checks
        let leftPos = hoverPos.x + 18;
        let topPos = hoverPos.y - 16;

        // Adjust horizontal position if too close to right edge
        if (leftPos + tooltipWidth > viewport.width - padding) {
          leftPos = hoverPos.x - 18 - tooltipWidth / 2;
        }

        // Adjust vertical position if too close to top
        if (topPos - tooltipHeight < padding) {
          topPos = hoverPos.y + 30; // Show below cursor instead
        }

        // Ensure it doesn't go off left edge
        if (leftPos < padding) {
          leftPos = padding;
        }

        return (
          <div
            className="pointer-events-none absolute px-3 py-2 rounded-md bg-neutral-900/95 border border-neutral-700 text-[11px] text-white/90 shadow-lg"
            style={{
              left: leftPos,
              top: topPos,
              transform: "translate(-50%, -100%)",
              transition: "left 80ms linear, top 80ms linear, opacity 120ms ease-out",
              opacity: 1,
              maxWidth: "320px",
            }}
          >
            <div>{`Agent #${n.id + 1}`}</div>
            {n.community_display_name && (
              <div className="mt-0.5 inline-block px-2 py-0.5 rounded-full bg-neutral-800 text-[9px] text-neutral-400 border border-neutral-700">
                {n.community_display_name}
              </div>
            )}
            {a && (
              <div className="mt-1 text-[10px] text-neutral-300">
                <div>{`Attention: ${a.attention}`}</div>
                <div
                  className="max-w-[300px] mt-1 leading-relaxed"
                  style={{
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                    whiteSpace: "normal"
                  }}
                >
                  {a.insight}
                </div>
              </div>
            )}
          </div>
        );
      })()}

      {/* Click card */}
      {activeNodeId !== null && (() => {
        const n = nodes.find((x) => x.id === activeNodeId);
        if (!n) return null;
        const a = analysisMap?.[n.id];

        // Calculate card dimensions
        const cardWidth = 420;
        const cardHeight = a ? 400 : 320; // taller if there's analysis info
        const padding = 16;
        const offsetX = 20;
        const offsetY = 20;

        // Start with preferred position (right and below)
        let leftPos = n.x + offsetX;
        let topPos = n.y + offsetY;

        // HORIZONTAL POSITIONING
        // Check if card would go off right edge
        if (leftPos + cardWidth > viewport.width - padding) {
          // Try left side of node
          const leftSidePos = n.x - cardWidth - offsetX;
          if (leftSidePos >= padding) {
            leftPos = leftSidePos;
          } else {
            // Clamp to right edge with padding
            leftPos = viewport.width - cardWidth - padding;
          }
        }

        // VERTICAL POSITIONING
        // Check if card would go off bottom edge
        if (topPos + cardHeight > viewport.height - padding) {
          // Try above node
          const abovePos = n.y - cardHeight - offsetY;
          if (abovePos >= padding) {
            topPos = abovePos;
          } else {
            // Clamp to bottom edge with padding
            topPos = viewport.height - cardHeight - padding;
          }
        }

        // Final safety clamps (should rarely trigger with above logic)
        leftPos = Math.max(padding, Math.min(leftPos, viewport.width - cardWidth - padding));
        topPos = Math.max(padding, Math.min(topPos, viewport.height - cardHeight - padding));

        return (
          <div
            className="absolute max-w-[420px] w-[420px] rounded-2xl bg-neutral-900/90 border border-neutral-700 shadow-2xl p-5"
            style={{ left: leftPos, top: topPos }}
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="text-2xl font-semibold">{`Agent #${n.id + 1}`}</div>
                {n.name && (
                  <div className="text-sm text-neutral-400 mt-1">{n.name}</div>
                )}
                {n.community_display_name && (
                  <div className="mt-2 inline-block px-3 py-1 rounded-full bg-neutral-800 text-xs text-neutral-300 border border-neutral-600">
                    {n.community_display_name}
                  </div>
                )}
              </div>
              <button
                className="text-neutral-400 hover:text-white text-2xl leading-none"
                onClick={() => setActiveNodeId(null)}
              >
                ×
              </button>
            </div>

            {/* Show attention info if available */}
            {a && (
              <div className="mt-3 p-3 rounded-lg bg-neutral-800/50 border border-neutral-700">
                <div className="text-sm text-neutral-300 mb-2">
                  <span className="text-neutral-400">Attention:</span>{" "}
                  <span className={
                    a.attention === "full" ? "text-green-400 font-medium" :
                    a.attention === "ignore" ? "text-red-400 font-medium" :
                    "text-gray-400 font-medium"
                  }>
                    {a.attention}
                  </span>
                </div>
                <div className="text-sm text-white italic">
                  &ldquo;{a.insight}&rdquo;
                </div>
              </div>
            )}

            <div className="mt-4 flex flex-wrap gap-2">
              <div className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 bg-neutral-800 border border-neutral-700 text-sm whitespace-nowrap">
                {n.gender}
              </div>
              <div className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 bg-neutral-800 border border-neutral-700 text-sm whitespace-nowrap">
                {n.ageRange}
              </div>
              <div className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 bg-neutral-800 border border-neutral-700 text-sm whitespace-nowrap">
                {n.incomeLevel}
              </div>
              {n.value1 && n.value1 !== "N/A" && (
                <div className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 bg-neutral-800 border border-neutral-700 text-sm whitespace-nowrap">
                  {n.value1}
                </div>
              )}
              {n.value2 && n.value2 !== "N/A" && (
                <div className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 bg-neutral-800 border border-neutral-700 text-sm whitespace-nowrap">
                  {n.value2}
                </div>
              )}
            </div>

            {/* Real persona summary */}
            {n.summary ? (
              <p className="mt-4 text-sm text-neutral-300 leading-relaxed">
                {n.summary}
              </p>
            ) : (
              <p className="mt-4 text-sm text-neutral-400 italic">
                No profile summary available.
              </p>
            )}

            {/* Show pain points and motivations if available */}
            {(n.pain_points && n.pain_points.length > 0) && (
              <div className="mt-4">
                <div className="text-xs font-semibold text-neutral-400 mb-2">Pain Points:</div>
                <div className="flex flex-wrap gap-1.5">
                  {n.pain_points.slice(0, 3).map((point, idx) => (
                    <span key={idx} className="text-xs px-2 py-1 rounded bg-red-900/30 text-red-300 border border-red-800/50">
                      {point}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {(n.motivations && n.motivations.length > 0) && (
              <div className="mt-3">
                <div className="text-xs font-semibold text-neutral-400 mb-2">Motivations:</div>
                <div className="flex flex-wrap gap-1.5">
                  {n.motivations.slice(0, 3).map((motivation, idx) => (
                    <span key={idx} className="text-xs px-2 py-1 rounded bg-green-900/30 text-green-300 border border-green-800/50">
                      {motivation}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })()}
    </div>
  );
}


