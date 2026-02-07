import { useState } from "react";
import { motion } from "framer-motion";
import { Search, Sliders, Plus, FileText, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import type { VectorSearchResult } from "@/types/api";

interface VectorSearchPanelProps {
  auditId: string;
}

// Mock search results
const mockResults: VectorSearchResult[] = [
  {
    chunk_id: "chunk_001",
    source_file: "Contract_v2.1.pdf",
    page: 7,
    snippet: "...the Provider shall maintain comprehensive insurance coverage including professional liability insurance of no less than $1,000,000 per occurrence...",
    similarity_score: 0.92,
  },
  {
    chunk_id: "chunk_002",
    source_file: "Tech_Specification.pdf",
    page: 3,
    snippet: "...data retention policy requires all customer data to be stored for a minimum of 7 years following contract termination...",
    similarity_score: 0.87,
  },
  {
    chunk_id: "chunk_003",
    source_file: "SLA_Addendum.docx",
    page: 5,
    snippet: "...scheduled maintenance windows shall not exceed 4 hours per month and must be communicated at least 72 hours in advance...",
    similarity_score: 0.81,
  },
  {
    chunk_id: "chunk_004",
    source_file: "Contract_v2.1.pdf",
    page: 15,
    snippet: "...intellectual property rights in any modifications or derivatives shall remain with the original rights holder unless explicitly assigned...",
    similarity_score: 0.76,
  },
];

export function VectorSearchPanel({ auditId }: VectorSearchPanelProps) {
  const [query, setQuery] = useState("");
  const [threshold, setThreshold] = useState([0.75]);
  const [results, setResults] = useState<VectorSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const { toast } = useToast();

  const handleSearch = async () => {
    if (!query.trim()) return;
    
    setIsSearching(true);
    // Simulate API call
    await new Promise((r) => setTimeout(r, 800));
    
    const filtered = mockResults.filter((r) => r.similarity_score >= threshold[0]);
    setResults(filtered);
    setIsSearching(false);
  };

  const handleAddAsFinding = (result: VectorSearchResult) => {
    toast({
      title: "Added as finding",
      description: `Chunk from ${result.source_file} added to findings.`,
    });
  };

  const getSimilarityColor = (score: number) => {
    if (score >= 0.9) return "text-success";
    if (score >= 0.8) return "text-primary";
    if (score >= 0.7) return "text-warning";
    return "text-muted-foreground";
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            Semantic Search
          </CardTitle>
          <CardDescription>
            Search across all documents using natural language. Find related clauses and hidden connections.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="e.g., liability limitations, data retention, termination clause..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="pl-9"
              />
            </div>
            <Button onClick={handleSearch} disabled={isSearching || !query.trim()}>
              {isSearching ? "Searching..." : "Search"}
            </Button>
          </div>

          <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/50">
            <Sliders className="h-4 w-4 text-muted-foreground" />
            <div className="flex-1">
              <Label className="text-sm">Similarity Threshold: {threshold[0].toFixed(2)}</Label>
              <Slider
                value={threshold}
                onValueChange={setThreshold}
                min={0.5}
                max={0.95}
                step={0.05}
                className="mt-2"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {results.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Results ({results.length})</h3>
            <Badge variant="secondary">
              Threshold: ≥{threshold[0].toFixed(2)}
            </Badge>
          </div>

          <div className="space-y-3">
            {results.map((result, index) => (
              <motion.div
                key={result.chunk_id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm font-medium">{result.source_file}</span>
                          <Badge variant="outline" className="text-xs">Page {result.page}</Badge>
                          <Badge variant="secondary" className={`${getSimilarityColor(result.similarity_score)} text-xs`}>
                            {(result.similarity_score * 100).toFixed(0)}% match
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{result.snippet}</p>
                      </div>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleAddAsFinding(result)}
                      >
                        <Plus className="h-4 w-4 mr-1" />
                        Add to Findings
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {results.length === 0 && query && !isSearching && (
        <Card className="border-dashed">
          <CardContent className="p-8 text-center">
            <Search className="h-12 w-12 mx-auto text-muted-foreground/50" />
            <p className="text-muted-foreground mt-4">No results found. Try a different query or lower the similarity threshold.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
