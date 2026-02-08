import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { 
  Upload, 
  FileText, 
  AlertTriangle, 
  CheckCircle2, 
  Sparkles,
  ArrowRight,
  Scale,
  Shield,
  Briefcase,
  Zap,
  TrendingUp
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuditResultStore } from "@/stores/auditResultStore";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" as const } }
};

export default function Dashboard() {
  const { flashcards, acceptedCards, response } = useAuditResultStore();
  
  const hasResults = flashcards.length > 0;
  const criticalCount = flashcards.filter(c => c.severity.toLowerCase() === 'critical').length;
  const highCount = flashcards.filter(c => c.severity.toLowerCase() === 'high').length;

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-8 max-w-6xl mx-auto"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">SpecGap AI Council</h1>
          <p className="text-muted-foreground mt-1">
            Upload contracts & specs to get AI-powered audit flashcards
          </p>
        </div>
        <Button asChild size="lg" className="bg-gradient-primary hover:opacity-90 transition-opacity shadow-glow group">
          <Link to="/upload">
            <Upload className="mr-2 h-4 w-4" />
            New Audit
            <ArrowRight className="ml-2 h-4 w-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
          </Link>
        </Button>
      </motion.div>

      {/* Hero CTA Card */}
      <motion.div variants={itemVariants}>
        <Card className="relative overflow-hidden border border-primary/20 bg-card">
          <div className="absolute inset-0 bg-gradient-glow pointer-events-none" />
          <div className="absolute top-0 right-0 w-1/3 h-full opacity-5 pointer-events-none"
            style={{ background: 'radial-gradient(circle at 80% 50%, hsl(var(--primary)), transparent 70%)' }}
          />
          <CardContent className="p-8 relative">
            <div className="flex items-center justify-between gap-8">
              <div className="flex items-center gap-6">
                <div className="flex -space-x-3">
                  {[
                    { icon: Scale, bg: 'bg-primary/15', text: 'text-primary', ring: 'ring-primary/20' },
                    { icon: Briefcase, bg: 'bg-success/15', text: 'text-success', ring: 'ring-success/20' },
                    { icon: Shield, bg: 'bg-warning/15', text: 'text-warning', ring: 'ring-warning/20' },
                  ].map((agent, i) => (
                    <motion.div
                      key={i}
                      initial={{ scale: 0, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ delay: 0.3 + i * 0.1, type: 'spring', stiffness: 200 }}
                      className={`flex h-14 w-14 items-center justify-center rounded-full ${agent.bg} ring-4 ring-background`}
                    >
                      <agent.icon className={`h-6 w-6 ${agent.text}`} />
                    </motion.div>
                  ))}
                </div>
                <div>
                  <h3 className="text-xl font-bold">
                    {hasResults ? "Start New Analysis" : "Welcome, ready for your first audit?"}
                  </h3>
                  <p className="text-muted-foreground mt-1 max-w-lg">
                    {hasResults 
                      ? "Upload another contract for the AI Council to review."
                      : "Upload a contract to let the AI Council analyze it for risks and gaps."}
                  </p>
                </div>
              </div>
              <Button asChild size="lg" className="bg-gradient-primary group shrink-0 shadow-md">
                <Link to="/upload">
                  <Zap className="mr-2 h-5 w-5" />
                  Start Analysis
                  <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Current Results */}
      {hasResults && (
        <motion.div variants={itemVariants} className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              Latest Audit Results
            </h2>
            <Button variant="outline" size="sm" asChild className="group">
              <Link to="/audit/results">
                View All Flashcards
                <ArrowRight className="ml-1 h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </Button>
          </div>
          
          <div className="grid gap-4 md:grid-cols-4">
            {[
              { label: "Total Issues Found", value: flashcards.length, color: "text-primary", gradient: "from-primary/10" },
              { label: "Critical", value: criticalCount, color: "text-risk-critical", gradient: "from-risk-critical/10" },
              { label: "High Priority", value: highCount, color: "text-risk-high", gradient: "from-risk-high/10" },
              { label: "Fixes Accepted", value: acceptedCards.length, color: "text-success", gradient: "from-success/10" },
            ].map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.05 }}
              >
                <Card className={`bg-gradient-to-br ${stat.gradient} to-transparent border-border/50 hover:shadow-md transition-shadow`}>
                  <CardContent className="p-5 text-center">
                    <div className={`text-3xl font-bold ${stat.color}`}>{stat.value}</div>
                    <div className="text-sm text-muted-foreground mt-0.5">{stat.label}</div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>

          {/* Recent Flashcards */}
          <div className="grid gap-3">
            {flashcards.slice(0, 3).map((card, index) => (
              <motion.div
                key={card.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.08 }}
              >
                <Card className="hover:shadow-md transition-all hover:border-border group">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                          card.severity.toLowerCase() === 'critical' ? 'bg-risk-critical/15' :
                          card.severity.toLowerCase() === 'high' ? 'bg-risk-high/15' :
                          'bg-risk-medium/15'
                        }`}>
                          <AlertTriangle className={`h-5 w-5 ${
                            card.severity.toLowerCase() === 'critical' ? 'text-risk-critical' :
                            card.severity.toLowerCase() === 'high' ? 'text-risk-high' :
                            'text-risk-medium'
                          }`} />
                        </div>
                        <div>
                          <p className="font-medium group-hover:text-primary transition-colors">{card.title}</p>
                          <p className="text-sm text-muted-foreground">{card.fix_action}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <Badge variant="secondary" className={
                          card.severity.toLowerCase() === 'critical' ? 'bg-risk-critical/10 text-risk-critical border-risk-critical/20' :
                          card.severity.toLowerCase() === 'high' ? 'bg-risk-high/10 text-risk-high border-risk-high/20' :
                          'bg-risk-medium/10 text-risk-medium border-risk-medium/20'
                        }>
                          {card.severity}
                        </Badge>
                        <Badge variant="outline" className="text-xs">{card.source_agent}</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* How It Works */}
      <motion.div variants={itemVariants}>
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <TrendingUp className="h-5 w-5 text-primary" />
              How SpecGap Works
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              {[
                { step: 1, title: "Upload Documents", desc: "Upload contracts, tech specs, or proposals (PDF, DOCX, TXT)" },
                { step: 2, title: "AI Council Analyzes", desc: "Three AI agents debate and identify risks, gaps, and issues" },
                { step: 3, title: "Review Flashcards", desc: "Swipe through issues and accept fixes with proposed language" },
              ].map((item, i) => (
                <motion.div
                  key={item.step}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + i * 0.1 }}
                  className="flex items-start gap-4 p-5 rounded-xl bg-muted/30 border border-border/30 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary font-bold text-sm">
                    {item.step}
                  </div>
                  <div>
                    <p className="font-semibold">{item.title}</p>
                    <p className="text-sm text-muted-foreground mt-1">{item.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Agent Council Info */}
      <motion.div variants={itemVariants}>
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="text-lg">AI Council Agents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              {[
                { icon: Scale, name: "Legal Agent", desc: "Liability, IP, contract traps", color: "text-primary", bg: "bg-primary/5", border: "border-primary/15" },
                { icon: Briefcase, name: "Business Agent", desc: "Operations, feasibility, risks", color: "text-success", bg: "bg-success/5", border: "border-success/15" },
                { icon: Shield, name: "Finance Agent", desc: "Hidden costs, ROI analysis", color: "text-warning", bg: "bg-warning/5", border: "border-warning/15" },
              ].map((agent, i) => (
                <motion.div
                  key={agent.name}
                  whileHover={{ y: -2 }}
                  className={`flex items-center gap-4 p-5 rounded-xl ${agent.bg} border ${agent.border} transition-shadow hover:shadow-md`}
                >
                  <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${agent.bg}`}>
                    <agent.icon className={`h-6 w-6 ${agent.color}`} />
                  </div>
                  <div>
                    <p className="font-semibold">{agent.name}</p>
                    <p className="text-sm text-muted-foreground">{agent.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
