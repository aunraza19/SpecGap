import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ArrowLeft, 
  FileText, 
  Clock, 
  AlertTriangle,
  Sparkles,
  Maximize2,
  Minimize2
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FlashcardStack } from "@/components/audit/FlashcardStack";
import { DeepAnalysisView } from "@/components/audit/DeepAnalysisView";
import { useAuditResultStore } from "@/stores/auditResultStore";
import type { Flashcard, FullSpectrumResponse } from "@/types/api";

export default function AuditResultsPage() {
  const navigate = useNavigate();
  const { response, flashcards, acceptedCards, rejectedCards } = useAuditResultStore();
  const hasFlashcards = response?.council_verdict?.flashcards?.length > 0;
  const [isFocusMode, setIsFocusMode] = useState(false);

  // Only enable focus mode if we have flashcards to show
  useEffect(() => {
    if (hasFlashcards) {
      setIsFocusMode(true);
    }
  }, [hasFlashcards]);

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
      {/* Focus Mode Overlay - only for quick analysis with flashcards */}
      <AnimatePresence>
        {isFocusMode && hasFlashcards && !isComplete && (
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
            {hasFlashcards ? 'Council Verdict' : 'Deep Analysis Report'}
          </h1>
          <p className="text-muted-foreground mt-1">
            {hasFlashcards 
              ? 'Review and accept AI-recommended fixes for your documents'
              : 'Detailed tech audit, legal analysis, and cross-check synthesis'
            }
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

      {/* Summary Stats - only when flashcards exist */}
      {hasFlashcards && (
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
      )}

      {/* Main Content Grid */}
      <div className={`grid gap-6 ${hasFlashcards ? 'lg:grid-cols-2' : 'lg:grid-cols-1'}`}>
        {/* Flashcard Review - only shown when flashcards exist */}
        {hasFlashcards && (
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
        )}

        {/* Deep Analysis — full rich view */}
        {fullResponse?.deep_analysis && (
          <div className={hasFlashcards ? '' : 'col-span-full'}>
            <DeepAnalysisView analysis={fullResponse.deep_analysis} />
          </div>
        )}
      </div>
    </div>
  );
}
