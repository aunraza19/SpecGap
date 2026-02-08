import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ArrowLeft, 
  FileText, 
  Clock, 
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  Maximize2,
  X,
  Minimize2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { FlashcardStack } from "@/components/audit/FlashcardStack";
import { MermaidRenderer } from "@/components/audit/MermaidRenderer";
import { useAuditResultStore } from "@/stores/auditResultStore";
import type { Flashcard, FullSpectrumResponse } from "@/types/api";

export default function AuditResultsPage() {
  const navigate = useNavigate();
  const { response, flashcards, acceptedCards, rejectedCards } = useAuditResultStore();
  const [isFocusMode, setIsFocusMode] = useState(true);

  // Redirect if no results
  useEffect(() => {
    if (!response) {
      navigate("/upload");
    }
  }, [response, navigate]);

  if (!response) return null;

  const isFullSpectrum = 'deep_analysis' in response;
  const fullResponse = isFullSpectrum ? (response as FullSpectrumResponse) : null;

  const criticalCount = flashcards.filter(c => 
    c.severity.toLowerCase() === 'critical'
  ).length;
  
  const highCount = flashcards.filter(c => 
    c.severity.toLowerCase() === 'high'
  ).length;

  const isComplete = flashcards.length > 0 && 
    (acceptedCards.length + rejectedCards.length === flashcards.length);

  const handleComplete = (accepted: Flashcard[], rejected: Flashcard[]) => {
    console.log("Review complete!", { accepted, rejected });
    setIsFocusMode(false); // Exit focus mode on completion
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6 relative">
      {/* Focus Mode Overlay */}
      <AnimatePresence>
        {isFocusMode && !isComplete && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur-xl p-4 supports-[backdrop-filter]:bg-background/60"
          >
            <div className="w-full max-w-lg relative">
               <div className="absolute -top-16 left-0 right-0 flex justify-between items-center text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-primary" />
                    <span className="font-medium text-foreground">Council Review Mode</span>
                  </div>
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    className="hover:bg-muted/20 hover:text-foreground"
                    onClick={() => setIsFocusMode(false)}
                  >
                    <Minimize2 className="w-4 h-4 mr-2" />
                    Minimize
                  </Button>
               </div>
               <FlashcardStack onComplete={handleComplete} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-start justify-between"
      >
        <div>
          <Button 
            variant="ghost" 
            size="sm" 
            className="mb-2"
            onClick={() => navigate("/upload")}
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Upload
          </Button>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Sparkles className="w-8 h-8 text-primary" />
            Council Verdict
          </h1>
          <p className="text-muted-foreground mt-1">
            Review and accept AI-recommended fixes for your documents
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="outline" className="gap-1.5 py-1.5">
            <FileText className="w-4 h-4" />
            {response.files_analyzed.length} files
          </Badge>
          <Badge variant="outline" className="gap-1.5 py-1.5">
            <Clock className="w-4 h-4" />
            {response.domain}
          </Badge>
        </div>
      </motion.div>

      {/* Summary Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        <Card className="bg-gradient-to-br from-primary/10 to-transparent border-primary/20">
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-primary">{flashcards.length}</div>
            <div className="text-sm text-muted-foreground">Total Issues</div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-red-500/10 to-transparent border-red-500/20">
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-red-500">{criticalCount}</div>
            <div className="text-sm text-muted-foreground">Critical</div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-orange-500/10 to-transparent border-orange-500/20">
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-orange-500">{highCount}</div>
            <div className="text-sm text-muted-foreground">High Priority</div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-500/10 to-transparent border-green-500/20">
          <CardContent className="p-4 text-center">
            <div className="text-3xl font-bold text-green-500">{acceptedCards.length}</div>
            <div className="text-sm text-muted-foreground">Accepted</div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Flashcard Review */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="h-full flex flex-col">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-primary" />
                  Issue Review
                </CardTitle>
                {!isComplete && !isFocusMode && (
                  <Button variant="outline" size="sm" onClick={() => setIsFocusMode(true)}>
                    <Maximize2 className="w-4 h-4 mr-2" />
                    Focus Mode
                  </Button>
                )}
              </div>
              <CardDescription>
                Swipe right to accept fixes, left to skip. Tap cards for details.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1">
              <FlashcardStack onComplete={handleComplete} />
            </CardContent>
          </Card>
        </motion.div>

        {/* Deep Analysis (if available) */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-6"
        >
          {/* Executive Synthesis */}
          {fullResponse?.deep_analysis?.executive_synthesis?.strategic_synthesis && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-green-500" />
                  Executive Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {fullResponse.deep_analysis.executive_synthesis.strategic_synthesis}
                </p>
                
                {fullResponse.deep_analysis.executive_synthesis.contradictions?.length > 0 && (
                  <>
                    <Separator />
                    <div>
                      <h4 className="font-medium mb-2">Key Contradictions Found</h4>
                      <ul className="space-y-2">
                        {fullResponse.deep_analysis.executive_synthesis.contradictions.map((c, i) => (
                          <li key={i} className="text-sm">
                            <span className="font-medium text-destructive">{c.topic || c.issue}:</span>{" "}
                            <span className="text-muted-foreground">{c.impact || c.description}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          )}

          {/* Mermaid Diagram */}
          {fullResponse?.deep_analysis?.executive_synthesis?.reality_diagram_mermaid && (
            <Card>
              <CardHeader>
                <CardTitle>Architecture Reality Check</CardTitle>
                <CardDescription>Visual representation of actual vs. proposed architecture</CardDescription>
              </CardHeader>
              <CardContent>
                <MermaidRenderer 
                  chart={fullResponse.deep_analysis.executive_synthesis.reality_diagram_mermaid} 
                />
              </CardContent>
            </Card>
          )}

          {/* Quick Stats */}
          {fullResponse?.deep_analysis && (
            <Card>
              <CardHeader>
                <CardTitle>Analysis Scores</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Ambiguity Score</span>
                  <Badge variant={
                    fullResponse.deep_analysis.tech_audit.ambiguity_score > 50 
                      ? "destructive" 
                      : "secondary"
                  }>
                    {fullResponse.deep_analysis.tech_audit.ambiguity_score}/100
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Leverage Score</span>
                  <Badge variant={
                    fullResponse.deep_analysis.legal_audit.leverage_score < 50 
                      ? "destructive" 
                      : "secondary"
                  }>
                    {fullResponse.deep_analysis.legal_audit.leverage_score}/100
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Favor Direction</span>
                  <Badge variant="outline">
                    {fullResponse.deep_analysis.legal_audit.favor_direction}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          )}
        </motion.div>
      </div>
    </div>
  );
}
