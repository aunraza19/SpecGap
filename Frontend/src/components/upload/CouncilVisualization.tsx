import { motion } from "framer-motion";
import { Scale, Briefcase, Shield } from "lucide-react";
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

export function CouncilVisualization({ isProcessing }: CouncilVisualizationProps) {
  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle className="text-lg">AI Council Session</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative py-8">
          {/* Connection Lines SVG */}
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none"
            style={{ zIndex: 0 }}
          >
            {isProcessing && (
              <>
                {/* Lines between agents */}
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
            {agents.map((agent, index) => (
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
            ))}
          </div>

          {/* Round Indicator */}
          {isProcessing && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-8 text-center"
            >
              <p className="text-sm text-muted-foreground">
                <span className="font-medium text-foreground">Round 1:</span> Independent Analysis
              </p>
              <div className="flex justify-center gap-2 mt-2">
                {[1, 2, 3].map((round) => (
                  <div
                    key={round}
                    className={`h-2 w-8 rounded-full ${
                      round === 1 ? "bg-primary" : "bg-muted"
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
