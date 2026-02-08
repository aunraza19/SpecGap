import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

interface MermaidRendererProps {
  chart: string;
}

mermaid.initialize({
  startOnLoad: false,
  theme: "neutral",
  securityLevel: "loose",
  fontFamily: "Inter, system-ui, sans-serif",
});

export function MermaidRenderer({ chart }: MermaidRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const renderChart = async () => {
      if (!chart) return;

      try {
        // Strip markdown code blocks if present
        let cleanChart = chart.replace(/```mermaid/g, "").replace(/```/g, "").trim();
        
        const id = `mermaid-${Date.now()}`;
        const { svg } = await mermaid.render(id, cleanChart);
        setSvg(svg);
        setError(null);
      } catch (err) {
        console.error("Mermaid rendering error:", err);
        setError("Failed to render visualization");
      }
    };

    renderChart();
  }, [chart]);

  if (error) {
    return (
      <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-sm">
        {error}
      </div>
    );
  }

  if (!chart) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        No diagram available
      </div>
    );
  }

  return (
    <div 
      ref={containerRef} 
      className="p-4 rounded-lg bg-muted/30 overflow-auto"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
