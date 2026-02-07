import { useState } from "react";
import { motion } from "framer-motion";
import { useParams, Link } from "react-router-dom";
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  Download,
  RefreshCw,
  MessageSquare,
  Search,
  ArrowLeft,
  ExternalLink,
  Scale,
  Briefcase,
  Shield,
  Copy,
  Mail,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { FindingsList } from "@/components/audit/FindingsList";
import { DocumentsList } from "@/components/audit/DocumentsList";
import { VectorSearchPanel } from "@/components/audit/VectorSearchPanel";
import { MermaidRenderer } from "@/components/audit/MermaidRenderer";
import { RedlineEditor } from "@/components/audit/RedlineEditor";
import { CommentsPanel } from "@/components/audit/CommentsPanel";
import type { Finding, AuditDocument } from "@/types/api";

// Mock data
const mockAuditDetail = {
  audit_id: "aud_001",
  project_name: "SaaS Platform Contract",
  status: "completed" as const,
  created_at: "2024-01-15T10:30:00Z",
  ambiguity_score: 78,
  leverage_score: 65,
  risk_score: 72,
  tech_report: {
    summary: "The technical specification includes several ambitious features that may conflict with contractual obligations. Key concerns include storage limitations, API rate limits, and deployment timelines.",
    findings: [],
    tech_stack_identified: ["React", "Node.js", "PostgreSQL", "AWS"],
    feasibility_score: 68,
  },
  legal_report: {
    summary: "Multiple clauses contain ambiguous language regarding liability, SLA commitments, and intellectual property rights. Immediate attention required on sections 4.2, 7.1, and 9.3.",
    findings: [],
    contract_type: "Software Development Agreement",
    jurisdiction: "Delaware, USA",
    risk_areas: ["Liability Cap", "IP Ownership", "SLA Penalties"],
  },
  patch_pack: {
    id: "patch_001",
    generated_at: "2024-01-15T11:00:00Z",
    patches: [],
    redline_content: `The Provider shall deliver "Unlimited Storage" as specified in Section 2.1.

PROPOSED CHANGE:
The Provider shall deliver storage capacity of up to 500GB per user account, with additional storage available at $0.10/GB/month, as specified in Section 2.1.

RATIONALE:
The term "Unlimited Storage" conflicts with the technical specification which implements local storage with defined limits. This amendment aligns contractual obligations with technical reality.`,
    email_draft: `Dear [Client Name],

Following our comprehensive review of the SaaS Platform Contract, we've identified several areas that require clarification to ensure alignment between contractual obligations and technical capabilities.

Key items for discussion:
1. Storage capacity definitions (Section 2.1)
2. API rate limit specifications (Section 3.4)
3. SLA penalty calculations (Section 7.1)

We recommend scheduling a call to discuss these amendments before proceeding.

Best regards`,
  },
  mermaid: `graph TD
    A[Contract Review] --> B{Gap Analysis}
    B --> C[Legal Gaps]
    B --> D[Tech Gaps]
    B --> E[Financial Gaps]
    C --> F[Section 2.1: Storage]
    C --> G[Section 7.1: SLA]
    D --> H[API Limits]
    D --> I[Deployment]
    E --> J[Cost Overruns]
    F --> K[CRITICAL: Unlimited vs 500GB]
    G --> K
    H --> K
    K --> L[Patch Pack Generated]`,
  documents: [
    { id: "doc_1", filename: "Contract_v2.1.pdf", file_type: "pdf", page_count: 24, size_bytes: 2456000, uploaded_at: "2024-01-15T10:30:00Z", ocr_processed: true },
    { id: "doc_2", filename: "Tech_Specification.pdf", file_type: "pdf", page_count: 15, size_bytes: 1834000, uploaded_at: "2024-01-15T10:30:00Z", ocr_processed: true },
    { id: "doc_3", filename: "SLA_Addendum.docx", file_type: "docx", page_count: 8, size_bytes: 456000, uploaded_at: "2024-01-15T10:30:00Z", ocr_processed: false },
  ] as AuditDocument[],
  comments: [],
};

const mockFindings: Finding[] = [
  {
    id: "find_001",
    category: "legal_trap",
    title: "Unlimited Storage vs Technical Reality",
    description: "Contract promises 'Unlimited Storage' but tech spec implements 500GB local storage limit.",
    risk_level: "critical",
    quote: "The Provider shall deliver Unlimited Storage capacity for all client data...",
    source_file: "Contract_v2.1.pdf",
    page: 5,
    agent_source: "legal",
    recommendations: ["Amend Section 2.1 to specify storage limits", "Add pricing tier for additional storage"],
  },
  {
    id: "find_002",
    category: "tech_gap",
    title: "API Rate Limit Ambiguity",
    description: "SLA guarantees 99.9% uptime but no rate limits defined. Risk of DDoS-induced SLA breach.",
    risk_level: "high",
    quote: "Provider guarantees 99.9% service availability measured monthly...",
    source_file: "SLA_Addendum.docx",
    page: 3,
    agent_source: "business",
    recommendations: ["Define API rate limits in technical appendix", "Add fair-use policy clause"],
  },
  {
    id: "find_003",
    category: "financial_risk",
    title: "Uncapped SLA Penalties",
    description: "Penalty clause has no liability cap. Theoretical exposure: $2.4M/year.",
    risk_level: "critical",
    quote: "For each hour of downtime exceeding the monthly allowance, Provider shall credit Client...",
    source_file: "SLA_Addendum.docx",
    page: 4,
    agent_source: "finance",
    recommendations: ["Add liability cap (suggest 12-month service fees)", "Define force majeure exclusions"],
  },
  {
    id: "find_004",
    category: "ambiguity",
    title: "Deployment Timeline Unclear",
    description: "Contract specifies 'reasonable time' for deployments without defining SLA.",
    risk_level: "medium",
    quote: "Updates shall be deployed within a reasonable timeframe following approval...",
    source_file: "Contract_v2.1.pdf",
    page: 12,
    agent_source: "legal",
    recommendations: ["Define specific deployment SLAs (e.g., 24h for critical, 7d for standard)"],
  },
  {
    id: "find_005",
    category: "legal_trap",
    title: "IP Assignment Scope Broad",
    description: "All 'work product' assigned to client—may include reusable code/libraries.",
    risk_level: "high",
    quote: "All Work Product created under this Agreement shall be the exclusive property of Client...",
    source_file: "Contract_v2.1.pdf",
    page: 18,
    agent_source: "legal",
    recommendations: ["Carve out pre-existing IP and standard libraries", "Define 'Work Product' explicitly"],
  },
];

export default function AuditDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState("overview");
  const audit = mockAuditDetail;

  const getRiskColor = (score: number) => {
    if (score >= 80) return "text-risk-critical";
    if (score >= 60) return "text-risk-high";
    if (score >= 40) return "text-risk-medium";
    return "text-risk-low";
  };

  const criticalCount = mockFindings.filter((f) => f.risk_level === "critical").length;
  const highCount = mockFindings.filter((f) => f.risk_level === "high").length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" asChild>
              <Link to="/audits">
                <ArrowLeft className="h-4 w-4" />
              </Link>
            </Button>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">{audit.project_name}</h1>
              <p className="text-sm text-muted-foreground">
                Created {new Date(audit.created_at).toLocaleDateString()} • {audit.documents.length} documents
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Re-run
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Score Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">Risk Score</p>
                <p className={`text-2xl font-bold ${getRiskColor(audit.risk_score || 0)}`}>
                  {audit.risk_score}%
                </p>
              </div>
              <div className="h-12 w-12 rounded-full bg-destructive/10 flex items-center justify-center">
                <AlertTriangle className="h-6 w-6 text-destructive" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">Ambiguity</p>
                <p className={`text-2xl font-bold ${getRiskColor(audit.ambiguity_score)}`}>
                  {audit.ambiguity_score}%
                </p>
              </div>
              <Progress value={audit.ambiguity_score} className="w-16 h-2" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">Leverage</p>
                <p className={`text-2xl font-bold ${getRiskColor(audit.leverage_score)}`}>
                  {audit.leverage_score}%
                </p>
              </div>
              <Progress value={audit.leverage_score} className="w-16 h-2" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">Findings</p>
                <p className="text-2xl font-bold">{mockFindings.length}</p>
              </div>
              <div className="flex gap-1">
                <Badge variant="destructive" className="text-xs">{criticalCount} critical</Badge>
                <Badge variant="secondary" className="bg-risk-high/10 text-risk-high text-xs">{highCount} high</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-6 lg:w-auto lg:inline-flex">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="findings">Findings</TabsTrigger>
          <TabsTrigger value="documents">Documents</TabsTrigger>
          <TabsTrigger value="search">Search</TabsTrigger>
          <TabsTrigger value="patch">Patch Pack</TabsTrigger>
          <TabsTrigger value="comments">Comments</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Summary Cards */}
          <div className="grid gap-6 lg:grid-cols-3">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Scale className="h-5 w-5 text-primary" />
                  Legal Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground">{audit.legal_report.summary}</p>
                <Separator />
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Risk Areas</p>
                  <div className="flex flex-wrap gap-1">
                    {audit.legal_report.risk_areas.map((area) => (
                      <Badge key={area} variant="secondary" className="text-xs">{area}</Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Briefcase className="h-5 w-5 text-success" />
                  Technical Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground">{audit.tech_report.summary}</p>
                <Separator />
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Tech Stack</p>
                  <div className="flex flex-wrap gap-1">
                    {audit.tech_report.tech_stack_identified.map((tech) => (
                      <Badge key={tech} variant="outline" className="text-xs">{tech}</Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Shield className="h-5 w-5 text-warning" />
                  Financial Impact
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-muted-foreground">
                  Identified potential financial exposure of $2.4M annually due to uncapped SLA penalties and ambiguous storage commitments.
                </p>
                <Separator />
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Feasibility Score</span>
                  <span className="font-semibold">{audit.tech_report.feasibility_score}%</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Mermaid Diagram */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Gap Analysis Flow</CardTitle>
              <CardDescription>Visual representation of identified gaps and their relationships</CardDescription>
            </CardHeader>
            <CardContent>
              <MermaidRenderer chart={audit.mermaid || ""} />
            </CardContent>
          </Card>

          {/* Quick Findings Preview */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">Critical Findings</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setActiveTab("findings")}>
                View All
                <ExternalLink className="h-4 w-4 ml-1" />
              </Button>
            </CardHeader>
            <CardContent>
              <FindingsList 
                findings={mockFindings.filter((f) => f.risk_level === "critical")} 
                compact 
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="findings">
          <FindingsList findings={mockFindings} />
        </TabsContent>

        <TabsContent value="documents">
          <DocumentsList documents={audit.documents} auditId={audit.audit_id} />
        </TabsContent>

        <TabsContent value="search">
          <VectorSearchPanel auditId={audit.audit_id} />
        </TabsContent>

        <TabsContent value="patch">
          <RedlineEditor 
            redlineContent={audit.patch_pack.redline_content || ""} 
            emailDraft={audit.patch_pack.email_draft || ""} 
          />
        </TabsContent>

        <TabsContent value="comments">
          <CommentsPanel auditId={audit.audit_id} findings={mockFindings} />
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
