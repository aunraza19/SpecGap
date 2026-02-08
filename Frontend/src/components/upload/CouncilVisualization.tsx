import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Scale, Briefcase, Shield, CheckCircle2, Clock, Loader2, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export interface CouncilVisualizationProps {
  isProcessing: boolean;
  error?: string | null;
  currentStageId?: string;
  mode?: "quick" | "deep";
}

const agents = [
  {
    id: "legal",
    name: "Legal Agent",
    icon: Scale,
    color: "text-primary",
    bgColor: "bg-primary/20",
    borderColor: "border-primary/40",
    description: "Contract analysis",
  },
  {
    id: "business",
    name: "Business Agent",
    icon: Briefcase,
    color: "text-success",
    bgColor: "bg-success/20",
    borderColor: "border-success/40",
    description: "Risk assessment",
  },
  {
    id: "finance",
    name: "Finance Agent",
    icon: Shield,
    color: "text-warning",
    bgColor: "bg-warning/20",
    borderColor: "border-warning/40",
    description: "Cost analysis",
  },
];

// Quick Scan Stages (Council Session -> Flashcards)
const quickStages = [
  { id: "upload", label: "Files Uploaded", emoji: "📤" },
  { id: "council", label: "AI Council Convened", emoji: "🏛️" },
  { id: "round1", label: "Round 1: Independent Analysis", emoji: "🔍" },
  { id: "round2", label: "Round 2: Cross-Check & Debate", emoji: "🗣️" },
  { id: "round3", label: "Round 3: Final Verdict", emoji: "⚖️" },
  { id: "synthesis", label: "Synthesizing Flashcards", emoji: "✨" },
];

// Deep Analysis Stages (Full Spectrum)
const fullStages = [
  { id: "upload", label: "Files Uploaded", emoji: "📤" },
  { id: "council", label: "AI Council Convened", emoji: "🏛️" },
  { id: "round1", label: "Round 1: Initial Scan", emoji: "🔍" },
  { id: "round2", label: "Round 2: Debate", emoji: "🗣️" },
  { id: "round3", label: "Round 3: Verdict", emoji: "⚖️" },
  { id: "tech_audit", label: "Tech Architect Inspection", emoji: "📐" },
  { id: "legal_audit", label: "Legal Leverage Analysis", emoji: "⚖️" },
  { id: "synthesis", label: "Final Executive Synthesis", emoji: "✨" },
];

// Sub-status messages for each round to make it feel alive
const roundMessages = {
  round1: ["Legal Agent analyzing risks...", "Business Agent reviewing terms...", "Finance Agent calculating impact..."],
  round2: ["Cross-checking findings...", "Debating contradictions...", "Validating with Tech Spec..."],
  round3: ["Voting on final verdict...", "Generating improved clauses...", "Finalizing risk score..."],
  tech_audit: ["Analyzing technical gaps...", "Verifying architectural alignment...", "Checking security compliance..."],
  legal_audit: ["Calculating leverage score...", "Identifying hidden liabilities...", "Reviewing indemnification clauses..."],
  synthesis: ["Compiling Executive Summary...", "Drawing Architecture Diagram...", "Preparing Patch Pack..."]
};

export function CouncilVisualization({ 
  isProcessing, 
  error, 
  currentStageId = "upload",
  mode = "quick" 
}: CouncilVisualizationProps) {
  const [subStatus, setSubStatus] = useState("");

  // Select stages based on mode
  const processingStages = mode === "deep" ? fullStages : quickStages;

  // Derive state from prop
  const currentStageIndex = processingStages.findIndex(s => s.id === currentStageId);
  
  // Hande case where stage might not be found (fallback to last known or 0)
  const safeIndex = currentStageIndex === -1 ? 0 : currentStageIndex;
  
  const currentStage = processingStages[safeIndex];
  
  // Completed stages must be STRICTLY before the current one
  const completedStages = processingStages
    .slice(0, safeIndex)
    .map(s => s.id);


  // Effect to cycle sub-status messages
  useEffect(() => {
    if (!isProcessing || !currentStage) return;
    
    // Safety check for indexing
    const messages = roundMessages[currentStage.id as keyof typeof roundMessages];
    if (!messages) {
      setSubStatus("");
      return;
    }

    let i = 0;
    setSubStatus(messages[0]);
    
    const interval = setInterval(() => {
      i = (i + 1) % messages.length;
      setSubStatus(messages[i]);
    }, 2000); // Change message every 2s

    return () => clearInterval(interval);
  }, [currentStage, isProcessing]);

  const isRoundActive = !error && (currentStage?.id.startsWith("round"));
  const currentRoundNum = parseInt(currentStage?.id.replace("round", "") || "0");

  return (
    <Card className="overflow-hidden border-primary/20">
      <CardHeader className={error ? "bg-destructive/10" : ""}>
        <CardTitle className="text-lg flex items-center gap-2">
          {error ? (
            <>
              <span className="text-destructive">Council Session Failed</span>
              <AlertCircle className="w-5 h-5 text-destructive" />
            </>
          ) : (
            <>
              AI Council Session
              {isProcessing && (
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
              )}
            </>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6 pt-6">
        {error && (
            <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-sm font-medium flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                {error}
            </div>
        )}

        {/* Real-time Processing Timeline */}
        <AnimatePresence>
          {isProcessing && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="bg-muted/30 rounded-lg p-4 border border-primary/20"
            >
              <p className="text-xs text-muted-foreground uppercase tracking-wider mb-3">
                Live Processing
              </p>
              <div className="space-y-2">
                {processingStages.map((stage, index) => {
                  const isCompleted = completedStages.includes(stage.id);
                  const isCurrent = index === safeIndex;
                  const isPending = index > safeIndex;

                  return (
                    <motion.div
                      key={stage.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={`
                        flex items-center gap-3 py-2 px-3 rounded-lg transition-all duration-300
                        ${isCurrent 
                          ? "bg-primary/10 border border-primary/50 shadow-[0_0_15px_-3px_rgba(59,130,246,0.3)] backdrop-blur-sm" 
                          : "border border-transparent"
                        }
                      `}
                    >
                      <span className="text-xl w-8 text-center">{stage.emoji}</span>
                      <span className={`flex-1 text-sm font-medium transition-colors ${
                        isCompleted ? "text-muted-foreground/60" :
                        isCurrent ? "text-primary" :
                        "text-muted-foreground"
                      }`}>
                        {stage.label}
                      </span>
                      
                      {isCompleted && (
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          transition={{ type: "spring", stiffness: 300, damping: 20 }}
                        >
                          <CheckCircle2 className="w-5 h-5 text-green-500" />
                        </motion.div>
                      )}
                      
                      {isCurrent && (
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                        >
                          <Loader2 className="w-5 h-5 text-primary" />
                        </motion.div>
                      )}
                      
                      {isPending && (
                        <div className="w-2 h-2 rounded-full bg-muted-foreground/20" />
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Agents Visualization */}
        <div className="relative py-4">
          {/* Connection Lines SVG */}
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none"
            style={{ zIndex: 0 }}
          >
            {isProcessing && (
              <>
                <motion.line
                  x1="25%"
                  y1="50%"
                  x2="50%"
                  y2="50%"
                  stroke="hsl(var(--primary))"
                  strokeWidth="2"
                  strokeDasharray="5,5"
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ pathLength: 1, opacity: 0.5 }}
                  transition={{ duration: 1, repeat: Infinity, repeatType: "reverse" }}
                />
                <motion.line
                  x1="50%"
                  y1="50%"
                  x2="75%"
                  y2="50%"
                  stroke="hsl(var(--success))"
                  strokeWidth="2"
                  strokeDasharray="5,5"
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ pathLength: 1, opacity: 0.5 }}
                  transition={{ duration: 1, delay: 0.3, repeat: Infinity, repeatType: "reverse" }}
                />
              </>
            )}
          </svg>

          {/* Agents Grid */}
          <div className="relative z-10 flex items-center justify-center gap-8">
            {agents.map((agent, index) => {
              // During rounds, ALL agents are active/thinking
              const isActive = isRoundActive || currentStage?.id === "synthesis";
              
              return (
                <motion.div
                  key={agent.id}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.2 }}
                  className="flex flex-col items-center gap-3"
                >
                  <motion.div
                    className={`
                      relative flex h-20 w-20 items-center justify-center rounded-full
                      border-2 ${agent.borderColor} ${agent.bgColor}
                      ${isActive ? "ring-2 ring-primary ring-offset-2" : ""}
                    `}
                    animate={isActive && isProcessing ? {
                      boxShadow: [
                        "0 0 0 0 hsla(var(--primary), 0)",
                        "0 0 20px 10px hsla(var(--primary), 0.2)",
                        "0 0 0 0 hsla(var(--primary), 0)",
                      ],
                    } : {}}
                    transition={{ duration: 2, repeat: Infinity, delay: index * 0.5 }}
                  >
                    <agent.icon className={`h-8 w-8 ${agent.color}`} />
                    
                    {isActive && isProcessing && (
                      <motion.div
                        className="absolute inset-0 rounded-full border-2 border-current opacity-30"
                        animate={{ scale: [1, 1.3, 1], opacity: [0.3, 0, 0.3] }}
                        transition={{ duration: 2, repeat: Infinity, delay: index * 0.3 }}
                        style={{ borderColor: "currentColor" }}
                      />
                    )}
                  </motion.div>
                  
                  <div className="text-center">
                    <p className="font-medium text-sm">{agent.name}</p>
                    <p className="text-xs text-muted-foreground">{agent.description}</p>
                  </div>

                  {isActive && isProcessing && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex items-center gap-1"
                    >
                      {[0, 1, 2].map((i) => (
                        <motion.div
                          key={i}
                          className="h-1.5 w-1.5 rounded-full bg-primary"
                          animate={{ opacity: [0.3, 1, 0.3] }}
                          transition={{ duration: 1, delay: i * 0.2, repeat: Infinity }}
                        />
                      ))}
                    </motion.div>
                  )}
                </motion.div>
              );
            })}
          </div>

          {/* Round Indicator with Dynamic Status */}
          {isProcessing && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 space-y-3"
            >
              <div className="text-center">
                <p className="text-sm text-foreground font-medium">
                  {currentStage?.label}
                </p>
                <div className="h-6 flex items-center justify-center">
                  <AnimatePresence mode="wait">
                    {subStatus && (
                      <motion.p
                        key={subStatus}
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -5 }}
                        className="text-xs text-muted-foreground italic"
                      >
                        {subStatus}
                      </motion.p>
                    )}
                  </AnimatePresence>
                </div>
              </div>

               {/* Stage Progress Bar */ }
               <div className="max-w-xs mx-auto h-1.5 bg-secondary rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-primary"
                    key={currentStage?.id} 
                    initial={{ width: "0%" }}
                    animate={{ width: "100%" }}
                    transition={{ 
                      duration: 10, // Approx duration, or use repeat for indeterminate
                      ease: "linear" 
                    }}
                  />
                </div>

              <div className="flex justify-center gap-2 mt-2">
                {[1, 2, 3].map((round) => (
                  <div
                    key={round}
                    className={`h-2 w-8 rounded-full transition-colors duration-500 ${
                      (currentRoundNum >= round) || (currentStage?.id === "synthesis") 
                        ? "bg-primary" 
                        : "bg-muted"
                    }`}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
