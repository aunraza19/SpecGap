import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { 
  CheckCircle2, 
  XCircle, 
  RotateCcw, 
  Download, 
  Scale, 
  Briefcase, 
  Banknote,
  Sparkles,
  FileText,
  FileIcon,
  Table as TableIcon
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FlashcardView } from "./FlashcardView";
import { useAuditResultStore } from "@/stores/auditResultStore";
import { cn } from "@/lib/utils";
import type { Flashcard } from "@/types/api";

interface FlashcardStackProps {
  onComplete?: (accepted: Flashcard[], rejected: Flashcard[]) => void;
}

const agentIcons = {
  legal: Scale,
  business: Briefcase,
  finance: Banknote,
};

export function FlashcardStack({ onComplete }: FlashcardStackProps) {
  const { 
    flashcards, 
    acceptedCards, 
    rejectedCards, 
    currentCardIndex,
    acceptCard,
    rejectCard,
    resetCards 
  } = useAuditResultStore();

  const [filter, setFilter] = useState<"all" | "legal" | "business" | "finance">("all");

  const filteredCards = useMemo(() => {
    if (filter === "all") return flashcards;
    return flashcards.filter(card => card.source_agent === filter);
  }, [flashcards, filter]);

  const remainingCards = useMemo(() => {
    const processedIds = new Set([
      ...acceptedCards.map(c => c.id),
      ...rejectedCards.map(c => c.id)
    ]);
    return filteredCards.filter(card => !processedIds.has(card.id));
  }, [filteredCards, acceptedCards, rejectedCards]);

  const currentCard = remainingCards[0];
  const isComplete = remainingCards.length === 0 && flashcards.length > 0;

  const handleAccept = (card: Flashcard) => {
    acceptCard(card);
    if (remainingCards.length === 1 && onComplete) {
      onComplete([...acceptedCards, card], rejectedCards);
    }
  };

  const handleReject = (card: Flashcard) => {
    rejectCard(card);
    if (remainingCards.length === 1 && onComplete) {
      onComplete(acceptedCards, [...rejectedCards, card]);
    }
  };

  const handleExportMarkdown = () => {
    const content = acceptedCards.map((card, i) => (
      `## ${i + 1}. ${card.title}\n\n` +
      `**Severity:** ${card.severity}\n` +
      `**Agent:** ${card.source_agent}\n` +
      `**Action:** ${card.fix_action}\n\n` +
      `### Description\n${card.description}\n\n` +
      `### Proposed Language\n> ${card.swipe_right_payload}\n\n---\n`
    )).join('\n');

    const blob = new Blob([`# Accepted Audit Fixes\n\n${content}`], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'accepted-fixes.md';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportPDF = () => {
    const doc = new jsPDF();
    
    // Header
    doc.setFontSize(20);
    doc.text("Audit Council Findings", 14, 22);
    doc.setFontSize(10);
    doc.text(`Generated on ${new Date().toLocaleDateString()}`, 14, 30);
    
    // Stats
    doc.text(`Total Accepted: ${acceptedCards.length}`, 14, 40);
    
    const tableData = acceptedCards.map(card => [
      card.title,
      card.severity,
      card.source_agent,
      card.fix_action,
      card.swipe_right_payload
    ]);

    autoTable(doc, {
      startY: 50,
      head: [['Issue', 'Severity', 'Agent', 'Action', 'Proposed Language']],
      body: tableData,
      headStyles: { fillColor: [66, 66, 66] },
      styles: { fontSize: 8 },
      columnStyles: {
        4: { cellWidth: 60 } // Widen the "Proposed Language" column
      }
    });

    doc.save("audit-findings.pdf");
  };

  if (flashcards.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <FileText className="w-16 h-16 text-muted-foreground/50 mb-4" />
        <h3 className="text-xl font-semibold text-muted-foreground">No flashcards yet</h3>
        <p className="text-sm text-muted-foreground/70 mt-2">
          Upload documents to generate audit flashcards
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filter Tabs */}
      <Tabs value={filter} onValueChange={(v) => setFilter(v as typeof filter)}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="all" className="gap-2">
            <Sparkles className="w-4 h-4" />
            All ({flashcards.length})
          </TabsTrigger>
          <TabsTrigger value="legal" className="gap-2">
            <Scale className="w-4 h-4" />
            Legal ({flashcards.filter(c => c.source_agent === 'legal').length})
          </TabsTrigger>
          <TabsTrigger value="business" className="gap-2">
            <Briefcase className="w-4 h-4" />
            Business ({flashcards.filter(c => c.source_agent === 'business').length})
          </TabsTrigger>
          <TabsTrigger value="finance" className="gap-2">
            <Banknote className="w-4 h-4" />
            Finance ({flashcards.filter(c => c.source_agent === 'finance').length})
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Progress Stats */}
      <div className="flex items-center justify-center gap-6">
        <div className="flex items-center gap-2 text-green-500">
          <CheckCircle2 className="w-5 h-5" />
          <span className="font-semibold">{acceptedCards.length}</span>
          <span className="text-muted-foreground text-sm">accepted</span>
        </div>
        <div className="h-4 w-px bg-border" />
        <div className="flex items-center gap-2 text-muted-foreground">
          <span className="font-semibold">{remainingCards.length}</span>
          <span className="text-sm">remaining</span>
        </div>
        <div className="h-4 w-px bg-border" />
        <div className="flex items-center gap-2 text-red-500">
          <XCircle className="w-5 h-5" />
          <span className="font-semibold">{rejectedCards.length}</span>
          <span className="text-muted-foreground text-sm">skipped</span>
        </div>
      </div>

      {/* Card Stack or Completion */}
      <AnimatePresence mode="wait">
        {isComplete ? (
          <motion.div
            key="complete"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center py-6 space-y-6"
          >
            <div className="flex items-center justify-center gap-2 mb-2">
              <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8 text-green-500" />
              </div>
            </div>
            
            <div>
              <h3 className="text-2xl font-bold">Review Complete!</h3>
              <p className="text-muted-foreground mt-1">
                You accepted {acceptedCards.length} fixes and skipped {rejectedCards.length}.
              </p>
            </div>

            {/* Summary Table */}
             <div className="rounded-md border bg-muted/20 text-left overflow-hidden">
              <div className="grid grid-cols-12 gap-4 p-3 font-medium text-sm bg-muted/50 border-b">
                <div className="col-span-1"></div>
                <div className="col-span-7">Issue</div>
                <div className="col-span-2">Severity</div>
                <div className="col-span-2">Action</div>
              </div>
              <ScrollArea className="h-[250px]">
                <div className="divide-y">
                  {acceptedCards.map((card, i) => (
                    <div key={card.id} className="grid grid-cols-12 gap-4 p-3 text-sm items-center hover:bg-muted/30">
                      <div className="col-span-1 flex justify-center">
                        <CheckCircle2 className="w-4 h-4 text-green-500" />
                      </div>
                      <div className="col-span-7 font-medium truncate" title={card.title}>
                        {card.title}
                      </div>
                      <div className="col-span-2">
                        <Badge variant="outline" className="text-xs scale-90 origin-left">
                          {card.severity}
                        </Badge>
                      </div>
                      <div className="col-span-2 text-xs text-muted-foreground truncate">
                        Accepted
                      </div>
                    </div>
                  ))}
                  {rejectedCards.map((card, i) => (
                    <div key={card.id} className="grid grid-cols-12 gap-4 p-3 text-sm items-center hover:bg-muted/30 opacity-60">
                      <div className="col-span-1 flex justify-center">
                        <XCircle className="w-4 h-4 text-muted-foreground" />
                      </div>
                       <div className="col-span-7 font-medium truncate" title={card.title}>
                        {card.title}
                      </div>
                      <div className="col-span-2">
                        <Badge variant="outline" className="text-xs scale-90 origin-left">
                          {card.severity}
                        </Badge>
                      </div>
                      <div className="col-span-2 text-xs text-muted-foreground">
                        Skipped
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>

            <div className="flex items-center justify-center gap-4 pt-4">
              <Button variant="outline" onClick={resetCards}>
                <RotateCcw className="w-4 h-4 mr-2" />
                Restart
              </Button>
              <Button onClick={handleExportMarkdown} variant="outline" className="gap-2">
                <FileIcon className="w-4 h-4" />
                MD
              </Button>
              <Button onClick={handleExportPDF} className="bg-gradient-primary gap-2">
                <Download className="w-4 h-4" />
                Download PDF
              </Button>
            </div>
          </motion.div>
        ) : currentCard ? (
          <FlashcardView
            key={currentCard.id}
            card={currentCard}
            onAccept={handleAccept}
            onReject={handleReject}
            index={filteredCards.length - remainingCards.length}
            total={filteredCards.length}
          />
        ) : null}
      </AnimatePresence>
    </div>
  );
}
