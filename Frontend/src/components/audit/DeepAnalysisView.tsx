import { useState } from "react";
import { motion } from "framer-motion";
import {
  Shield,
  AlertTriangle,
  Scale,
  Lightbulb,
  Copy,
  Check,
  Mail,
  Ticket,
  Bug,
  BookOpen,
  TrendingDown,
  TrendingUp,
  Zap,
  FileWarning,
  ArrowRight,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MermaidRenderer } from "@/components/audit/MermaidRenderer";
import type { FullSpectrumResponse } from "@/types/api";

interface DeepAnalysisViewProps {
  analysis: FullSpectrumResponse["deep_analysis"];
}

// ── Helpers ──

const severityBadgeVariant = (severity: string): "destructive" | "secondary" | "outline" => {
  switch (severity?.toLowerCase()) {
    case "critical":
    case "highest":
      return "destructive";
    case "high":
      return "destructive";
    case "medium":
      return "secondary";
    default:
      return "outline";
  }
};

const priorityIcon = (priority: string) => {
  switch (priority?.toLowerCase()) {
    case "highest":
      return "🔴";
    case "high":
      return "🟠";
    case "medium":
      return "🟡";
    case "low":
      return "🔵";
    default:
      return "⚪";
  }
};

// ── Component ──

export function DeepAnalysisView({ analysis }: DeepAnalysisViewProps) {
  const [copiedEmail, setCopiedEmail] = useState(false);
  const [copiedTicket, setCopiedTicket] = useState<string | null>(null);

  if (!analysis) return null;

  const { tech_audit, legal_audit } = analysis;

  // Normalize UPPERCASE keys (belt & suspenders — client.ts also normalizes)
  const rawSynthesis: any = analysis.executive_synthesis || {};
  const synthesis = {
    contradictions: rawSynthesis.CONTRADICTIONS || rawSynthesis.contradictions || [],
    strategic_synthesis: rawSynthesis.STRATEGIC_SYNTHESIS || rawSynthesis.strategic_synthesis || "",
    reality_diagram_mermaid: rawSynthesis.REALITY_DIAGRAM_MERMAID || rawSynthesis.reality_diagram_mermaid || "",
    patch_pack: rawSynthesis.PATCH_PACK || rawSynthesis.patch_pack || null,
  };

  const totalGaps = tech_audit?.critical_gaps?.length || 0;
  const totalTraps = legal_audit?.trap_clauses?.length || 0;
  const criticalTraps =
    legal_audit?.trap_clauses?.filter(
      (t) => t.severity?.toLowerCase() === "critical"
    ).length || 0;

  const handleCopyEmail = () => {
    const email = synthesis.patch_pack?.negotiation_email;
    if (email) {
      navigator.clipboard.writeText(email);
      setCopiedEmail(true);
      setTimeout(() => setCopiedEmail(false), 2000);
    }
  };

  const handleCopyTicket = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedTicket(id);
    setTimeout(() => setCopiedTicket(null), 2000);
  };

  // ── Stagger animation ──
  const stagger = (i: number) => ({ delay: 0.05 * i });

  return (
    <div className="space-y-6">
      {/* ═══════════════ Score Dashboard ═══════════════ */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 md:grid-cols-5 gap-4"
      >
        {/* Project Name */}
        {tech_audit?.project_name && (
          <Card className="col-span-2 md:col-span-1 bg-gradient-to-br from-primary/10 to-transparent border-primary/20">
            <CardContent className="p-4 text-center">
              <div className="text-xs text-muted-foreground mb-1">Project</div>
              <div className="text-lg font-bold text-primary truncate">
                {tech_audit.project_name}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Ambiguity Score */}
        <Card className="bg-gradient-to-br from-orange-500/10 to-transparent border-orange-500/20">
          <CardContent className="p-4 text-center space-y-2">
            <div className="text-xs text-muted-foreground">Ambiguity</div>
            <div className="text-3xl font-bold text-orange-500">
              {tech_audit?.ambiguity_score ?? "—"}
              <span className="text-sm font-normal text-muted-foreground">/100</span>
            </div>
            <Progress
              value={tech_audit?.ambiguity_score || 0}
              className="h-1.5 [&>div]:bg-orange-500"
            />
          </CardContent>
        </Card>

        {/* Leverage Score */}
        <Card className="bg-gradient-to-br from-purple-500/10 to-transparent border-purple-500/20">
          <CardContent className="p-4 text-center space-y-2">
            <div className="text-xs text-muted-foreground">Leverage</div>
            <div className="text-3xl font-bold text-purple-500">
              {legal_audit?.leverage_score ?? "—"}
              <span className="text-sm font-normal text-muted-foreground">/100</span>
            </div>
            <Progress
              value={legal_audit?.leverage_score || 0}
              className="h-1.5 [&>div]:bg-purple-500"
            />
          </CardContent>
        </Card>

        {/* Favor Direction */}
        <Card
          className={`bg-gradient-to-br ${
            legal_audit?.favor_direction?.toLowerCase() === "vendor"
              ? "from-red-500/10 border-red-500/20"
              : "from-green-500/10 border-green-500/20"
          } to-transparent`}
        >
          <CardContent className="p-4 text-center">
            <div className="text-xs text-muted-foreground mb-1">Favor</div>
            <div
              className={`text-lg font-bold flex items-center justify-center gap-1 ${
                legal_audit?.favor_direction?.toLowerCase() === "vendor"
                  ? "text-red-500"
                  : "text-green-500"
              }`}
            >
              {legal_audit?.favor_direction?.toLowerCase() === "vendor" ? (
                <TrendingDown className="w-5 h-5" />
              ) : (
                <TrendingUp className="w-5 h-5" />
              )}
              {legal_audit?.favor_direction || "—"}
            </div>
          </CardContent>
        </Card>

        {/* Risk Summary */}
        <Card className="bg-gradient-to-br from-red-500/10 to-transparent border-red-500/20">
          <CardContent className="p-4 text-center">
            <div className="text-xs text-muted-foreground mb-1">Risks Found</div>
            <div className="text-3xl font-bold text-red-500">{totalGaps + totalTraps}</div>
            <div className="text-xs text-muted-foreground">
              {totalGaps} gaps · {totalTraps} traps
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* ═══════════════ Strategic Synthesis ═══════════════ */}
      {synthesis.strategic_synthesis && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={stagger(1)}>
          <Card className="border-primary/20">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-primary" />
                Strategic Synthesis
              </CardTitle>
              <CardDescription>AI-generated executive overview of the deal</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {synthesis.strategic_synthesis}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ═══════════════ Contradictions ═══════════════ */}
      {synthesis.contradictions?.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={stagger(2)}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-destructive" />
                Key Contradictions ({synthesis.contradictions.length})
              </CardTitle>
              <CardDescription>
                Conflicts between documents that create legal or technical risk
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {synthesis.contradictions.map((c: any, i: number) => (
                <div
                  key={i}
                  className="p-4 rounded-lg border border-destructive/20 bg-destructive/5 space-y-1"
                >
                  <div className="font-medium text-destructive flex items-center gap-2">
                    <FileWarning className="w-4 h-4 shrink-0" />
                    {c.topic || c.issue}
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {c.impact || c.description}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ═══════════════ Architecture Diagram ═══════════════ */}
      {synthesis.reality_diagram_mermaid && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={stagger(3)}>
          <Card>
            <CardHeader>
              <CardTitle>Architecture Reality Check</CardTitle>
              <CardDescription>
                Visual representation of actual vs. proposed architecture
              </CardDescription>
            </CardHeader>
            <CardContent>
              <MermaidRenderer chart={synthesis.reality_diagram_mermaid} />
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ═══════════════ Tech Gaps + Trap Clauses ═══════════════ */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Critical Gaps (Tech Audit) */}
        {tech_audit?.critical_gaps?.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={stagger(4)}>
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bug className="w-5 h-5 text-orange-500" />
                  Critical Tech Gaps ({tech_audit.critical_gaps.length})
                </CardTitle>
                <CardDescription>
                  Technical deficiencies detected by the Architect Agent
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Accordion type="multiple" className="w-full">
                  {tech_audit.critical_gaps.map((gap, i) => (
                    <AccordionItem key={i} value={`gap-${i}`}>
                      <AccordionTrigger className="hover:no-underline">
                        <div className="flex items-center gap-3 text-left">
                          <Badge variant={severityBadgeVariant(gap.risk_level)} className="shrink-0">
                            {gap.risk_level}
                          </Badge>
                          <span className="text-sm font-medium">{gap.feature}</span>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="space-y-3 pt-2">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                            Missing Component
                          </div>
                          <p className="text-sm font-medium">{gap.missing_component}</p>
                        </div>
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                            Recommendation
                          </div>
                          <p className="text-sm text-muted-foreground">{gap.recommendation}</p>
                        </div>
                        {gap.source_reference && (
                          <div className="p-3 rounded bg-muted/50 border text-xs text-muted-foreground italic">
                            <BookOpen className="w-3 h-3 inline mr-1.5" />
                            {gap.source_reference}
                          </div>
                        )}
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Trap Clauses (Legal Audit) */}
        {legal_audit?.trap_clauses?.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={stagger(5)}>
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Scale className="w-5 h-5 text-red-500" />
                  Trap Clauses ({legal_audit.trap_clauses.length})
                  {criticalTraps > 0 && (
                    <Badge variant="destructive" className="ml-auto">
                      {criticalTraps} Critical
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription>
                  Dangerous contract clauses detected by the Lawyer Agent
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Accordion type="multiple" className="w-full">
                  {legal_audit.trap_clauses.map((trap, i) => (
                    <AccordionItem key={i} value={`trap-${i}`}>
                      <AccordionTrigger className="hover:no-underline">
                        <div className="flex items-center gap-3 text-left">
                          <Badge
                            variant={severityBadgeVariant(trap.severity)}
                            className="shrink-0"
                          >
                            {trap.severity}
                          </Badge>
                          <span className="text-sm font-medium line-clamp-1">
                            {trap.clause_snippet}
                          </span>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="space-y-4 pt-2">
                        <p className="text-sm text-muted-foreground">{trap.risk_explanation}</p>

                        {trap.redline_suggestion && (
                          <div className="space-y-3">
                            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                              Redline Suggestion
                            </div>

                            {/* Original → Proposed diff */}
                            <div className="rounded-lg border overflow-hidden">
                              <div className="p-3 bg-red-500/5 border-b border-red-500/20">
                                <div className="text-xs font-medium text-red-500 mb-1 flex items-center gap-1">
                                  <span>✕</span> Original
                                </div>
                                <p className="text-sm line-through text-muted-foreground">
                                  {trap.redline_suggestion.original_text}
                                </p>
                              </div>
                              <div className="p-3 bg-green-500/5">
                                <div className="text-xs font-medium text-green-500 mb-1 flex items-center gap-1">
                                  <span>✓</span> Proposed
                                </div>
                                <p className="text-sm text-foreground">
                                  {trap.redline_suggestion.proposed_text}
                                </p>
                              </div>
                            </div>

                            {/* Negotiation argument */}
                            <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
                              <div className="text-xs font-semibold uppercase tracking-wider text-amber-600 mb-1">
                                Negotiation Argument
                              </div>
                              <p className="text-sm italic text-muted-foreground">
                                &ldquo;{trap.redline_suggestion.negotiation_argument}&rdquo;
                              </p>
                            </div>
                          </div>
                        )}
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>

      {/* ═══════════════ Negotiation Tips ═══════════════ */}
      {legal_audit?.negotiation_tips?.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={stagger(6)}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-yellow-500" />
                Negotiation Tips
              </CardTitle>
              <CardDescription>AI-recommended tactics for your next meeting</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 md:grid-cols-2">
                {legal_audit.negotiation_tips.map((tip, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-3 rounded-lg bg-yellow-500/5 border border-yellow-500/20"
                  >
                    <span className="shrink-0 w-6 h-6 rounded-full bg-yellow-500/20 text-yellow-600 text-xs font-bold flex items-center justify-center">
                      {i + 1}
                    </span>
                    <p className="text-sm text-muted-foreground">{tip}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* ═══════════════ Action Pack: JIRA + Email ═══════════════ */}
      {synthesis.patch_pack && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={stagger(7)}>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Ticket className="w-5 h-5 text-primary" />
                Action Pack
              </CardTitle>
              <CardDescription>Auto-generated deliverables ready to use</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="tickets" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="tickets" className="gap-2">
                    <Bug className="w-4 h-4" />
                    JIRA Tickets ({synthesis.patch_pack.jira_tickets?.length || 0})
                  </TabsTrigger>
                  <TabsTrigger value="email" className="gap-2">
                    <Mail className="w-4 h-4" />
                    Negotiation Email
                  </TabsTrigger>
                </TabsList>

                {/* ── JIRA Tickets Tab ── */}
                <TabsContent value="tickets" className="space-y-3 mt-4">
                  {synthesis.patch_pack.jira_tickets?.map((ticket: any, i: number) => (
                    <div
                      key={i}
                      className="p-4 rounded-lg border bg-card hover:bg-muted/30 transition-colors group"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-2 flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-base">{priorityIcon(ticket.priority)}</span>
                            <Badge
                              variant={severityBadgeVariant(ticket.priority)}
                              className="shrink-0 text-xs"
                            >
                              {ticket.priority}
                            </Badge>
                            <span className="font-semibold text-sm">
                              {ticket.summary || ticket.title}
                            </span>
                          </div>
                          <p className="text-sm text-muted-foreground">{ticket.description}</p>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={() =>
                            handleCopyTicket(
                              `${ticket.summary || ticket.title}\n\n${ticket.description}`,
                              `ticket-${i}`
                            )
                          }
                        >
                          {copiedTicket === `ticket-${i}` ? (
                            <Check className="w-4 h-4 text-green-500" />
                          ) : (
                            <Copy className="w-4 h-4" />
                          )}
                        </Button>
                      </div>
                    </div>
                  ))}
                </TabsContent>

                {/* ── Negotiation Email Tab ── */}
                <TabsContent value="email" className="mt-4">
                  {synthesis.patch_pack.negotiation_email && (
                    <div className="relative">
                      <Button
                        variant="outline"
                        size="sm"
                        className="absolute top-3 right-3 z-10 gap-2"
                        onClick={handleCopyEmail}
                      >
                        {copiedEmail ? (
                          <>
                            <Check className="w-4 h-4 text-green-500" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4" />
                            Copy
                          </>
                        )}
                      </Button>
                      <pre className="p-4 pr-24 rounded-lg border bg-muted/30 text-sm whitespace-pre-wrap font-mono leading-relaxed max-h-[500px] overflow-auto">
                        {synthesis.patch_pack.negotiation_email}
                      </pre>
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
