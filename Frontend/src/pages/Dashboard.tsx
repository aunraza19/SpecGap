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
  Zap
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuditResultStore } from "@/stores/auditResultStore";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
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
      className="space-y-8"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">SpecGap AI Council</h1>
          <p className="text-muted-foreground mt-1">
            Upload contracts & specs to get AI-powered audit flashcards
          </p>
        </div>
        <Button asChild className="bg-gradient-primary hover:opacity-90 transition-opacity">
          <Link to="/upload">
            <Upload className="mr-2 h-4 w-4" />
            New Audit
          </Link>
        </Button>
      </motion.div>

      {/* Main CTA Card */}
      <motion.div variants={itemVariants}>
        <Card className="relative overflow-hidden border-2 border-primary/30 bg-gradient-to-br from-primary/5 via-primary/10 to-transparent">
          <div className="absolute inset-0 bg-gradient-glow pointer-events-none" />
          <CardContent className="p-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div className="flex -space-x-2">
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-purple-500/20 ring-4 ring-background">
                    <Scale className="h-7 w-7 text-purple-400" />
                  </div>
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-blue-500/20 ring-4 ring-background">
                    <Briefcase className="h-7 w-7 text-blue-400" />
                  </div>
                  <div className="flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/20 ring-4 ring-background">
                    <Shield className="h-7 w-7 text-emerald-400" />
                  </div>
                </div>
                <div>
                  <h3 className="text-xl font-bold">Upload Documents to Start</h3>
                  <p className="text-muted-foreground mt-1 max-w-md">
                    Our 3-Agent AI Council (Legal, Business, Finance) will analyze your contracts 
                    and generate actionable flashcards with recommended fixes.
                  </p>
                </div>
              </div>
              <Button asChild size="lg" className="bg-gradient-primary group">
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

      {/* Current Results (if any) */}
      {hasResults && (
        <motion.div variants={itemVariants}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-primary" />
              Latest Audit Results
            </h2>
            <Button variant="outline" size="sm" asChild>
              <Link to="/audit/results">
                View All Flashcards
                <ArrowRight className="ml-1 h-4 w-4" />
              </Link>
            </Button>
          </div>
          
          <div className="grid gap-4 md:grid-cols-4">
            <Card className="bg-gradient-to-br from-primary/10 to-transparent border-primary/20">
              <CardContent className="p-4 text-center">
                <div className="text-3xl font-bold text-primary">{flashcards.length}</div>
                <div className="text-sm text-muted-foreground">Total Issues Found</div>
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
                <div className="text-sm text-muted-foreground">Fixes Accepted</div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Flashcards Preview */}
          <div className="grid gap-3 mt-4">
            {flashcards.slice(0, 3).map((card, index) => (
              <motion.div
                key={card.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                          card.severity.toLowerCase() === 'critical' ? 'bg-red-500/20' :
                          card.severity.toLowerCase() === 'high' ? 'bg-orange-500/20' :
                          'bg-yellow-500/20'
                        }`}>
                          <AlertTriangle className={`h-5 w-5 ${
                            card.severity.toLowerCase() === 'critical' ? 'text-red-500' :
                            card.severity.toLowerCase() === 'high' ? 'text-orange-500' :
                            'text-yellow-500'
                          }`} />
                        </div>
                        <div>
                          <p className="font-medium">{card.title}</p>
                          <p className="text-sm text-muted-foreground">{card.fix_action}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <Badge variant="secondary" className={
                          card.severity.toLowerCase() === 'critical' ? 'bg-red-500/10 text-red-500' :
                          card.severity.toLowerCase() === 'high' ? 'bg-orange-500/10 text-orange-500' :
                          'bg-yellow-500/10 text-yellow-500'
                        }>
                          {card.severity}
                        </Badge>
                        <Badge variant="outline">{card.source_agent}</Badge>
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
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              How SpecGap Works
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="flex items-start gap-4 p-4 rounded-lg bg-muted/50">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-bold">
                  1
                </div>
                <div>
                  <p className="font-medium">Upload Documents</p>
                  <p className="text-sm text-muted-foreground">
                    Upload contracts, tech specs, or proposals (PDF, DOCX, TXT)
                  </p>
                </div>
              </div>
              
              <div className="flex items-start gap-4 p-4 rounded-lg bg-muted/50">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-bold">
                  2
                </div>
                <div>
                  <p className="font-medium">AI Council Analyzes</p>
                  <p className="text-sm text-muted-foreground">
                    Three AI agents debate and identify risks, gaps, and issues
                  </p>
                </div>
              </div>
              
              <div className="flex items-start gap-4 p-4 rounded-lg bg-muted/50">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-bold">
                  3
                </div>
                <div>
                  <p className="font-medium">Review Flashcards</p>
                  <p className="text-sm text-muted-foreground">
                    Swipe through issues and accept fixes with proposed language
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Agent Council Info */}
      <motion.div variants={itemVariants}>
        <Card>
          <CardHeader>
            <CardTitle>AI Council Agents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="flex items-center gap-4 p-4 rounded-lg bg-purple-500/5 border border-purple-500/20">
                <Scale className="h-8 w-8 text-purple-400" />
                <div>
                  <p className="font-medium">Legal Agent</p>
                  <p className="text-sm text-muted-foreground">Liability, IP, contract traps</p>
                </div>
              </div>
              <div className="flex items-center gap-4 p-4 rounded-lg bg-blue-500/5 border border-blue-500/20">
                <Briefcase className="h-8 w-8 text-blue-400" />
                <div>
                  <p className="font-medium">Business Agent</p>
                  <p className="text-sm text-muted-foreground">Operations, feasibility, risks</p>
                </div>
              </div>
              <div className="flex items-center gap-4 p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                <Shield className="h-8 w-8 text-emerald-400" />
                <div>
                  <p className="font-medium">Finance Agent</p>
                  <p className="text-sm text-muted-foreground">Hidden costs, ROI analysis</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
