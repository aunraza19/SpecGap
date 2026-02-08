import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  Upload,
  ArrowRight,
  Sparkles,
  Clock,
  RefreshCw,
  AlertCircle,
  History,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuditResultStore } from "@/stores/auditResultStore";
import { auditApi } from "@/api/client";

interface PastAudit {
  id: string;
  created_at: string | null;
  project_name: string | null;
  audit_type: string;
  tech_spec_filename: string | null;
  risk_level: string | null;
  composite_risk_score: number | null;
  status: string;
}

export default function AuditsPage() {
  const { flashcards, acceptedCards, rejectedCards, response } = useAuditResultStore();
  const [pastAudits, setPastAudits] = useState<PastAudit[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const hasResults = flashcards.length > 0;
  const criticalCount = flashcards.filter(c => c.severity.toLowerCase() === 'critical').length;
  const highCount = flashcards.filter(c => c.severity.toLowerCase() === 'high').length;

  // Fetch past audits from database
  useEffect(() => {
    const fetchAudits = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await auditApi.list({ limit: 20 });
        setPastAudits(response.audits || []);
      } catch (err) {
        console.error("Failed to fetch audits:", err);
        setError("Failed to load audit history");
      } finally {
        setIsLoading(false);
      }
    };
    fetchAudits();
  }, []);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Unknown date";
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getRiskBadgeVariant = (riskLevel: string | null) => {
    switch (riskLevel?.toLowerCase()) {
      case "critical": return "destructive";
      case "high": return "destructive";
      case "medium": return "outline";
      default: return "secondary";
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Audit Results</h1>
          <p className="text-muted-foreground mt-1">
            View your AI-analyzed contract audits
          </p>
        </div>
        <Button asChild className="bg-gradient-primary">
          <Link to="/upload">
            <Upload className="mr-2 h-4 w-4" />
            New Audit
          </Link>
        </Button>
      </div>

      {hasResults && (
        <>
          {/* Current Audit Stats */}
          <Card className="border-primary/30 bg-gradient-to-br from-primary/5 to-transparent">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-primary" />
                    Current Audit Results
                  </CardTitle>
                  <CardDescription className="mt-1">
                    {response?.files_analyzed?.length || 0} files analyzed • {response?.domain || 'Unknown domain'}
                  </CardDescription>
                </div>
                <Button asChild>
                  <Link to="/audit/results">
                    Review Flashcards
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-5">
                <div className="text-center p-4 rounded-lg bg-muted/50">
                  <div className="text-2xl font-bold">{flashcards.length}</div>
                  <div className="text-sm text-muted-foreground">Total Issues</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-red-500/10">
                  <div className="text-2xl font-bold text-red-500">{criticalCount}</div>
                  <div className="text-sm text-muted-foreground">Critical</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-orange-500/10">
                  <div className="text-2xl font-bold text-orange-500">{highCount}</div>
                  <div className="text-sm text-muted-foreground">High</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-green-500/10">
                  <div className="text-2xl font-bold text-green-500">{acceptedCards.length}</div>
                  <div className="text-sm text-muted-foreground">Accepted</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-muted/50">
                  <div className="text-2xl font-bold text-muted-foreground">{rejectedCards.length}</div>
                  <div className="text-sm text-muted-foreground">Skipped</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Flashcard List */}
          <Card>
            <CardHeader>
              <CardTitle>All Findings</CardTitle>
              <CardDescription>
                Issues identified by the AI Council
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {flashcards.map((card, index) => {
                  const isAccepted = acceptedCards.some(c => c.id === card.id);
                  const isRejected = rejectedCards.some(c => c.id === card.id);
                  
                  return (
                    <motion.div
                      key={card.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="flex items-center justify-between p-4 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                          card.severity.toLowerCase() === 'critical' ? 'bg-red-500/20' :
                          card.severity.toLowerCase() === 'high' ? 'bg-orange-500/20' :
                          card.severity.toLowerCase() === 'medium' ? 'bg-yellow-500/20' :
                          'bg-green-500/20'
                        }`}>
                          <AlertTriangle className={`h-5 w-5 ${
                            card.severity.toLowerCase() === 'critical' ? 'text-red-500' :
                            card.severity.toLowerCase() === 'high' ? 'text-orange-500' :
                            card.severity.toLowerCase() === 'medium' ? 'text-yellow-500' :
                            'text-green-500'
                          }`} />
                        </div>
                        <div>
                          <p className="font-medium">{card.title}</p>
                          <p className="text-sm text-muted-foreground">{card.description.substring(0, 100)}...</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <Badge variant="outline">{card.source_agent}</Badge>
                        <Badge className={
                          card.severity.toLowerCase() === 'critical' ? 'bg-red-500' :
                          card.severity.toLowerCase() === 'high' ? 'bg-orange-500' :
                          card.severity.toLowerCase() === 'medium' ? 'bg-yellow-500 text-black' :
                          'bg-green-500'
                        }>
                          {card.severity}
                        </Badge>
                        {isAccepted && (
                          <Badge className="bg-green-500/20 text-green-500">
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Accepted
                          </Badge>
                        )}
                        {isRejected && (
                          <Badge variant="secondary">Skipped</Badge>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Audit History from Database */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5 text-muted-foreground" />
                Audit History
              </CardTitle>
              <CardDescription>
                Previously completed audits saved in the database
              </CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={() => window.location.reload()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              <RefreshCw className="h-5 w-5 animate-spin mr-2" />
              Loading audit history...
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-8 text-destructive">
              <AlertCircle className="h-5 w-5 mr-2" />
              {error}
            </div>
          ) : pastAudits.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
              <FileText className="h-10 w-10 mb-3 opacity-50" />
              <p>No audit history yet</p>
              <p className="text-sm mt-1">Complete an audit to see it here</p>
            </div>
          ) : (
            <div className="space-y-3">
              <AnimatePresence>
                {pastAudits.map((audit, index) => (
                  <motion.div
                    key={audit.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ delay: index * 0.05 }}
                    className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-muted/30 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                        <FileText className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium">
                          {audit.project_name || audit.tech_spec_filename || "Untitled Audit"}
                        </p>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          {formatDate(audit.created_at)}
                          <span>•</span>
                          <span className="capitalize">{audit.audit_type?.replace("_", " ")}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      {audit.risk_level && (
                        <Badge variant={getRiskBadgeVariant(audit.risk_level)}>
                          {audit.risk_level}
                        </Badge>
                      )}
                      {audit.composite_risk_score !== null && (
                        <Badge variant="outline">
                          Risk: {audit.composite_risk_score}
                        </Badge>
                      )}
                      <Badge variant={audit.status === "completed" ? "secondary" : "outline"}>
                        {audit.status}
                      </Badge>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Empty State - Only show if no current results AND no past audits */}
      {!hasResults && pastAudits.length === 0 && !isLoading && (
        <Card className="border-dashed border-2">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <FileText className="h-16 w-16 text-muted-foreground/50 mb-4" />
            <h3 className="text-xl font-semibold">No Audits Yet</h3>
            <p className="text-muted-foreground mt-2 max-w-md">
              Upload your contracts and technical specifications to have the AI Council analyze them for risks, gaps, and issues.
            </p>
            <Button asChild className="mt-6 bg-gradient-primary">
              <Link to="/upload">
                <Upload className="mr-2 h-4 w-4" />
                Start Your First Audit
              </Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
}
