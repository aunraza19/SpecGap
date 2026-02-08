import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Scale, Briefcase, Shield, CheckCircle2, Clock, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface CouncilVisualizationProps {
  isProcessing: boolean;
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

// Processing stages for real-time timeline
const processingStages = [
  { id: "upload", label: "Files Uploaded", emoji: "📤", duration: 1000 },
  { id: "council", label: "AI Council Convened", emoji: "🏛️", duration: 2000 },
  { id: "legal", label: "Legal Agent Analyzing", emoji: "⚖️", duration: 3000 },
  { id: "business", label: "Business Agent Analyzing", emoji: "💼", duration: 3000 },
  { id: "finance", label: "Finance Agent Analyzing", emoji: "💰", duration: 3000 },
  { id: "synthesis", label: "Synthesizing Verdict", emoji: "✨", duration: 2000 },
];

export function CouncilVisualization({ isProcessing }: CouncilVisualizationProps) {
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [completedStages, setCompletedStages] = useState<string[]>([]);

  // Progress through stages when processing
  useEffect(() => {
    if (!isProcessing) {
      setCurrentStageIndex(0);
      setCompletedStages([]);
      return;
    }

    // Simulate progress through stages
    const stage = processingStages[currentStageIndex];
    if (!stage) return;

    const timer = setTimeout(() => {
      setCompletedStages(prev => [...prev, stage.id]);
      if (currentStageIndex < processingStages.length - 1) {
        setCurrentStageIndex(prev => prev + 1);
      }
    }, stage.duration);

    return () => clearTimeout(timer);
  }, [isProcessing, currentStageIndex]);

  const currentStage = processingStages[currentStageIndex];

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          AI Council Session
          {isProcessing && (
            <Loader2 className="w-4 h-4 animate-spin text-primary" />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
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
                  const isCurrent = index === currentStageIndex;
                  const isPending = index > currentStageIndex;

                  return (
                    <motion.div
                      key={stage.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={`flex items-center gap-3 py-1.5 px-2 rounded transition-colors ${
                        isCurrent ? "bg-primary/10 border border-primary/30" : ""
                      }`}
                    >
                      <span className="text-lg w-6">{stage.emoji}</span>
                      <span className={`flex-1 text-sm ${
                        isCompleted ? "text-muted-foreground line-through" :
                        isCurrent ? "text-foreground font-medium" :
                        "text-muted-foreground"
                      }`}>
                        {stage.label}
                      </span>
                      {isCompleted && (
                        <CheckCircle2 className="w-4 h-4 text-green-500" />
                      )}
                      {isCurrent && (
                        <motion.div
                          animate={{ opacity: [0.5, 1, 0.5] }}
                          transition={{ duration: 1, repeat: Infinity }}
                        >
                          <Clock className="w-4 h-4 text-primary" />
                        </motion.div>
                      )}
                      {isPending && (
                        <div className="w-4 h-4 rounded-full border border-muted-foreground/30" />
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
              const isAgentActive = currentStage?.id === agent.id;
              
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
                      ${isAgentActive ? "ring-2 ring-primary ring-offset-2" : ""}
                    `}
                    animate={isProcessing ? {
                      boxShadow: [
                        "0 0 0 0 hsla(var(--primary), 0)",
                        "0 0 20px 10px hsla(var(--primary), 0.2)",
                        "0 0 0 0 hsla(var(--primary), 0)",
                      ],
                    } : {}}
                    transition={{ duration: 2, repeat: Infinity, delay: index * 0.5 }}
                  >
                    <agent.icon className={`h-8 w-8 ${agent.color}`} />
                    
                    {isProcessing && (
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

                  {isProcessing && (
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

          {/* Round Indicator */}
          {isProcessing && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6 text-center"
            >
              <p className="text-sm text-muted-foreground">
                <span className="font-medium text-foreground">
                  {currentStage?.id === "synthesis" ? "Final Synthesis" : `Round ${Math.min(currentStageIndex, 3)}:`}
                </span>{" "}
                {currentStage?.id === "synthesis" 
                  ? "Generating Consensus Verdict" 
                  : currentStageIndex <= 2 
                    ? "Independent Analysis"
                    : "Cross-Verification"}
              </p>
              <div className="flex justify-center gap-2 mt-2">
                {[1, 2, 3].map((round) => (
                  <div
                    key={round}
                    className={`h-2 w-8 rounded-full ${
                      round <= Math.ceil((currentStageIndex + 1) / 2) ? "bg-primary" : "bg-muted"
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
