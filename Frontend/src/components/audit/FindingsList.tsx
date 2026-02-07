import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { 
  AlertTriangle, 
  FileText, 
  ExternalLink,
  Scale,
  Briefcase,
  Shield,
  ChevronRight
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Finding, RiskLevel } from "@/types/api";

interface FindingsListProps {
  findings: Finding[];
  compact?: boolean;
  onFindingClick?: (finding: Finding) => void;
}

const riskConfig: Record<RiskLevel, { label: string; color: string; bgColor: string }> = {
  critical: { label: "Critical", color: "text-risk-critical", bgColor: "bg-risk-critical/10" },
  high: { label: "High", color: "text-risk-high", bgColor: "bg-risk-high/10" },
  medium: { label: "Medium", color: "text-risk-medium", bgColor: "bg-risk-medium/10" },
  low: { label: "Low", color: "text-risk-low", bgColor: "bg-risk-low/10" },
  info: { label: "Info", color: "text-risk-info", bgColor: "bg-risk-info/10" },
};

const agentConfig = {
  legal: { icon: Scale, color: "text-primary", label: "Legal Agent" },
  business: { icon: Briefcase, color: "text-success", label: "Business Agent" },
  finance: { icon: Shield, color: "text-warning", label: "Finance Agent" },
};

const categoryLabels = {
  tech_gap: "Tech Gap",
  legal_trap: "Legal Trap",
  financial_risk: "Financial Risk",
  ambiguity: "Ambiguity",
};

export function FindingsList({ findings, compact = false, onFindingClick }: FindingsListProps) {
  // Group findings by category
  const grouped = findings.reduce((acc, finding) => {
    const category = finding.category;
    if (!acc[category]) acc[category] = [];
    acc[category].push(finding);
    return acc;
  }, {} as Record<string, Finding[]>);

  if (compact) {
    return (
      <div className="space-y-3">
        {findings.slice(0, 3).map((finding, index) => (
          <motion.div
            key={finding.id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <FindingCard finding={finding} compact onClick={onFindingClick} />
          </motion.div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {Object.entries(grouped).map(([category, categoryFindings]) => (
        <div key={category} className="space-y-4">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold">{categoryLabels[category as keyof typeof categoryLabels]}</h3>
            <Badge variant="secondary">{categoryFindings.length}</Badge>
          </div>
          <div className="space-y-3">
            {categoryFindings.map((finding, index) => (
              <motion.div
                key={finding.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <FindingCard finding={finding} onClick={onFindingClick} />
              </motion.div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

interface FindingCardProps {
  finding: Finding;
  compact?: boolean;
  onClick?: (finding: Finding) => void;
}

function FindingCard({ finding, compact = false, onClick }: FindingCardProps) {
  const risk = riskConfig[finding.risk_level];
  const agent = agentConfig[finding.agent_source];
  const AgentIcon = agent.icon;

  return (
    <Card 
      className={`
        group hover:shadow-md transition-all cursor-pointer
        ${risk.bgColor} border-l-4
        ${finding.risk_level === "critical" ? "border-l-risk-critical" : ""}
        ${finding.risk_level === "high" ? "border-l-risk-high" : ""}
        ${finding.risk_level === "medium" ? "border-l-risk-medium" : ""}
        ${finding.risk_level === "low" ? "border-l-risk-low" : ""}
      `}
      onClick={() => onClick?.(finding)}
    >
      <CardContent className={compact ? "p-4" : "p-5"}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="secondary" className={`${risk.color} ${risk.bgColor}`}>
                <AlertTriangle className="h-3 w-3 mr-1" />
                {risk.label}
              </Badge>
              <Badge variant="outline" className="text-xs">
                <AgentIcon className={`h-3 w-3 mr-1 ${agent.color}`} />
                {agent.label}
              </Badge>
            </div>
            
            <h4 className="font-semibold group-hover:text-primary transition-colors">
              {finding.title}
            </h4>
            
            {!compact && (
              <>
                <p className="text-sm text-muted-foreground">{finding.description}</p>
                
                <blockquote className="border-l-2 border-muted pl-3 text-sm italic text-muted-foreground">
                  "{finding.quote}"
                </blockquote>

                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <FileText className="h-3 w-3" />
                    {finding.source_file}
                  </span>
                  <span>Page {finding.page}</span>
                </div>

                {finding.recommendations.length > 0 && (
                  <div className="pt-2">
                    <p className="text-xs font-medium text-muted-foreground mb-1">Recommendations:</p>
                    <ul className="text-sm space-y-1">
                      {finding.recommendations.map((rec, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <ChevronRight className="h-4 w-4 shrink-0 text-primary mt-0.5" />
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>

          <Button variant="ghost" size="icon" className="shrink-0" asChild>
            <Link to={`documents/${encodeURIComponent(finding.source_file)}?page=${finding.page}&finding=${finding.id}`}>
              <ExternalLink className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
