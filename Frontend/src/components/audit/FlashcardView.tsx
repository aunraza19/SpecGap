import { motion, useMotionValue, useTransform, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { Check, X, Scale, Briefcase, Banknote, AlertTriangle, AlertCircle, Info, SkipForward } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Flashcard } from "@/types/api";

interface FlashcardViewProps {
  card: Flashcard;
  onAccept: (card: Flashcard) => void;
  onReject: (card: Flashcard) => void;
  index: number;
  total: number;
}

const severityConfig = {
  critical: {
    gradient: "from-red-500/20 via-red-600/10 to-transparent",
    border: "border-red-500/50",
    badge: "bg-red-500 text-white",
    icon: AlertTriangle,
  },
  high: {
    gradient: "from-orange-500/20 via-orange-600/10 to-transparent",
    border: "border-orange-500/50",
    badge: "bg-orange-500 text-white",
    icon: AlertCircle,
  },
  medium: {
    gradient: "from-yellow-500/20 via-yellow-600/10 to-transparent",
    border: "border-yellow-500/50",
    badge: "bg-yellow-500 text-black",
    icon: AlertCircle,
  },
  low: {
    gradient: "from-green-500/20 via-green-600/10 to-transparent",
    border: "border-green-500/50",
    badge: "bg-green-500 text-white",
    icon: Info,
  },
};

const agentConfig = {
  legal: {
    icon: Scale,
    label: "Legal Counsel",
    color: "text-purple-400",
    bg: "bg-purple-500/10",
  },
  business: {
    icon: Briefcase,
    label: "Business Ops",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
  },
  finance: {
    icon: Banknote,
    label: "Finance",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
  },
};

export function FlashcardView({ card, onAccept, onReject, index, total }: FlashcardViewProps) {
  const [isFlipped, setIsFlipped] = useState(false);
  const [exitDirection, setExitDirection] = useState<"left" | "right" | null>(null);
  
  const x = useMotionValue(0);
  const rotate = useTransform(x, [-200, 200], [-15, 15]);
  const opacity = useTransform(x, [-200, -100, 0, 100, 200], [0.5, 1, 1, 1, 0.5]);
  
  const acceptOpacity = useTransform(x, [0, 100], [0, 1]);
  const rejectOpacity = useTransform(x, [-100, 0], [1, 0]);

  const severity = card.severity.toLowerCase() as keyof typeof severityConfig;
  const config = severityConfig[severity] || severityConfig.medium;
  const agent = agentConfig[card.source_agent];
  const AgentIcon = agent.icon;
  const SeverityIcon = config.icon;

  const handleDragEnd = (_: any, info: { offset: { x: number }; velocity: { x: number } }) => {
    const threshold = 100;
    if (info.offset.x > threshold || info.velocity.x > 500) {
      setExitDirection("right");
      onAccept(card);
    } else if (info.offset.x < -threshold || info.velocity.x < -500) {
      setExitDirection("left");
      onReject(card);
    }
  };

  return (
    <div className="relative w-full max-w-md mx-auto perspective-1000">
      {/* Background indicators */}
      <motion.div 
        className="absolute inset-0 flex items-center justify-start pl-4 pointer-events-none"
        style={{ opacity: rejectOpacity }}
      >
        <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center">
          <X className="w-8 h-8 text-red-500" />
        </div>
      </motion.div>
      
      <motion.div 
        className="absolute inset-0 flex items-center justify-end pr-4 pointer-events-none"
        style={{ opacity: acceptOpacity }}
      >
        <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center">
          <Check className="w-8 h-8 text-green-500" />
        </div>
      </motion.div>

      <AnimatePresence mode="wait">
        <motion.div
          key={card.id}
          className={cn(
            "relative cursor-grab active:cursor-grabbing",
            "rounded-2xl border-2 backdrop-blur-sm",
            "bg-gradient-to-br",
            config.gradient,
            config.border,
            "shadow-xl shadow-black/20"
          )}
          style={{ x, rotate, opacity }}
          drag="x"
          dragConstraints={{ left: 0, right: 0 }}
          dragElastic={0.7}
          onDragEnd={handleDragEnd}
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ 
            x: exitDirection === "right" ? 300 : exitDirection === "left" ? -300 : 0,
            opacity: 0,
            scale: 0.8,
            transition: { duration: 0.3 }
          }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setIsFlipped(!isFlipped)}
        >
          <div className="p-6 min-h-[400px] flex flex-col">
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className={cn(
                "flex items-center gap-2 px-3 py-1.5 rounded-full text-sm",
                agent.bg,
                agent.color
              )}>
                <AgentIcon className="w-4 h-4" />
                <span className="font-medium">{agent.label}</span>
              </div>
              
              <div className={cn(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-bold",
                config.badge
              )}>
                <SeverityIcon className="w-4 h-4" />
                {card.severity}
              </div>
            </div>

            {/* Card Type */}
            <div className="text-xs uppercase tracking-wider text-muted-foreground mb-2">
              {card.card_type}
            </div>

            {/* Title */}
            <h3 className="text-xl font-bold text-foreground mb-3 leading-tight">
              {card.title}
            </h3>

            {/* Description */}
            <p className="text-muted-foreground text-sm leading-relaxed flex-1">
              {card.description}
            </p>

            {/* Fix Action */}
            <div className="mt-4 pt-4 border-t border-white/10">
              <div className="text-xs uppercase tracking-wider text-muted-foreground mb-2">
                Recommended Action
              </div>
              <div className="flex items-center gap-2 text-primary font-semibold">
                <Check className="w-4 h-4" />
                {card.fix_action}
              </div>
            </div>

            {/* Payload Preview (flipped state) */}
            {isFlipped && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 p-4 rounded-lg bg-black/30 border border-white/10"
              >
                <div className="text-xs uppercase tracking-wider text-muted-foreground mb-2">
                  Proposed Contract Language
                </div>
                <p className="text-sm text-foreground/90 italic leading-relaxed">
                  "{card.swipe_right_payload}"
                </p>
              </motion.div>
            )}

            {/* Progress indicator */}
            <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
              <span>Tap for details</span>
              <span>{index + 1} of {total}</span>
            </div>
          </div>
        </motion.div>
      </AnimatePresence>

      {/* Action buttons */}
      <div className="flex items-center justify-center gap-6 mt-6">
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => {
            setExitDirection("left");
            onReject(card);
          }}
          title="Skip for now"
          className="w-14 h-14 rounded-full bg-muted/10 border-2 border-muted-foreground/30 flex items-center justify-center text-muted-foreground hover:bg-muted/20 transition-colors"
        >
          <SkipForward className="w-6 h-6" />
        </motion.button>

        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => {
            setExitDirection("right");
            onAccept(card);
          }}
          className="w-14 h-14 rounded-full bg-green-500/10 border-2 border-green-500/50 flex items-center justify-center text-green-500 hover:bg-green-500/20 transition-colors"
        >
          <Check className="w-6 h-6" />
        </motion.button>
      </div>
    </div>
  );
}
