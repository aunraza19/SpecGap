import { useState } from "react";
import { motion } from "framer-motion";
import { Search, Sliders, FileText, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";

export default function GlobalSearchPage() {
  const [query, setQuery] = useState("");
  const [threshold, setThreshold] = useState([0.75]);

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Global Search</h1>
        <p className="text-muted-foreground mt-1">Search across all audits using semantic similarity.</p>
      </div>

      <Card>
        <CardContent className="p-6 space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Search across all documents..." value={query} onChange={(e) => setQuery(e.target.value)} className="pl-9 text-lg h-12" />
            </div>
            <Button size="lg" className="bg-gradient-primary">Search</Button>
          </div>
          <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/50">
            <Sliders className="h-4 w-4" />
            <span className="text-sm">Threshold: {threshold[0].toFixed(2)}</span>
            <Slider value={threshold} onValueChange={setThreshold} min={0.5} max={0.95} step={0.05} className="w-48" />
          </div>
        </CardContent>
      </Card>

      <Card className="border-dashed">
        <CardContent className="p-12 text-center">
          <Search className="h-16 w-16 mx-auto text-muted-foreground/30" />
          <p className="text-muted-foreground mt-4">Enter a search query to find related content across all audits.</p>
        </CardContent>
      </Card>
    </motion.div>
  );
}
