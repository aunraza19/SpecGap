import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { 
  Upload, 
  File, 
  X, 
  FileText, 
  AlertCircle, 
  CheckCircle2,
  Loader2,
  Settings,
  Info
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { useUploadStore } from "@/stores/uploadStore";
import { useAuditResultStore } from "@/stores/auditResultStore";
import { CouncilVisualization } from "@/components/upload/CouncilVisualization";
import { auditApi } from "@/api/client";

const ACCEPTED_TYPES = [".pdf", ".docx", ".txt"];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const domains = [
  "Software Engineering",
  "Healthcare",
  "Finance & Banking",
  "Legal Services",
  "Construction",
  "Consulting",
  "E-commerce",
  "Manufacturing",
];

export default function UploadPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isDragging, setIsDragging] = useState(false);
  const [showCouncil, setShowCouncil] = useState(false);
  const [analysisMode, setAnalysisMode] = useState<"quick" | "deep">("quick");
  
  const {
    files,
    projectName,
    forceOcr,
    domain,
    isUploading,
    addFiles,
    removeFile,
    setProjectName,
    setForceOcr,
    setDomain,
    updateFileProgress,
    updateFileStatus,
    addFileLog,
    setIsUploading,
    clearFiles,
  } = useUploadStore();

  const { setResponse } = useAuditResultStore();

  const validateFile = (file: File): string | null => {
    const extension = `.${file.name.split(".").pop()?.toLowerCase()}`;
    if (!ACCEPTED_TYPES.includes(extension)) {
      return `Invalid file type. Accepted: ${ACCEPTED_TYPES.join(", ")}`;
    }
    if (file.size > MAX_FILE_SIZE) {
      return `File too large. Max size: ${MAX_FILE_SIZE / 1024 / 1024}MB`;
    }
    return null;
  };

  const handleFiles = useCallback((newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    const validFiles: File[] = [];
    
    fileArray.forEach((file) => {
      const error = validateFile(file);
      if (error) {
        toast({
          title: "Invalid file",
          description: `${file.name}: ${error}`,
          variant: "destructive",
        });
      } else {
        validFiles.push(file);
      }
    });

    if (validFiles.length > 0) {
      addFiles(validFiles);
    }
  }, [addFiles, toast]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  }, [handleFiles]);

  const handleUpload = async () => {
    if (files.length === 0) {
      toast({
        title: "No files selected",
        description: "Please add at least one document to analyze.",
        variant: "destructive",
      });
      return;
    }

    setIsUploading(true);
    setShowCouncil(true);

    // Update file statuses to uploading
    for (const fileProgress of files) {
      updateFileStatus(fileProgress.file.name, "uploading");
      addFileLog(fileProgress.file.name, "Uploading to server...");
      updateFileProgress(fileProgress.file.name, 50);
    }

    try {
      // Get raw files from the store
      const rawFiles = files.map(f => f.file);

      // Mark files as processing
      for (const fileProgress of files) {
        updateFileProgress(fileProgress.file.name, 100);
        updateFileStatus(fileProgress.file.name, "processing");
        addFileLog(fileProgress.file.name, "AI Council is analyzing...");
      }

      // Call the real API
      const response = analysisMode === "deep"
        ? await auditApi.fullSpectrum(rawFiles, domain)
        : await auditApi.councilSession(rawFiles, domain);

      if (response.status === "error") {
        throw new Error(response.message || "Analysis failed");
      }

      // Mark all files as complete
      files.forEach((f) => {
        updateFileStatus(f.file.name, "completed");
        addFileLog(f.file.name, "Analysis complete!");
      });

      // Validate response structure
      if (!response || !response.council_verdict) {
        throw new Error("Invalid response from server (missing council verdict)");
      }

      const flashcards = response.council_verdict.flashcards || [];
      
      if (flashcards.length === 0) {
        // Warning but proceed, or throw error?
        // Let's warn but allow proceeding so user can see "0 issues" state if valid
        console.warn("[Upload] No flashcards generated by backend");
        toast({
          title: "Analysis Complete (0 Issues)",
          description: "Propably a parsing error or the document is perfect (unlikely). Check console logs.",
          variant: "default", 
        });
      } else {
        toast({
          title: "Audit Complete!",
          description: `Found ${flashcards.length} issues to review.`,
        });
      }

      // Store the response
      setResponse(response);

      setIsUploading(false);

      // Navigate to results page
      setTimeout(() => {
        navigate("/audit/results");
      }, 500);

    } catch (error) {
      console.error("Upload error:", error);
      
      files.forEach((f) => {
        updateFileStatus(f.file.name, "error");
        addFileLog(f.file.name, `Error: ${error instanceof Error ? error.message : "Unknown error"}`);
      });

      setIsUploading(false);
      setShowCouncil(false);

      toast({
        title: "Analysis Failed",
        description: error instanceof Error ? error.message : "Failed to analyze documents. Please try again.",
        variant: "destructive",
      });
    }
  };


  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-3xl font-bold tracking-tight">Upload Documents</h1>
        <p className="text-muted-foreground mt-1">
          Add contracts, tech specs, and agreements for AI Council analysis.
        </p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Upload Area */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-2 space-y-6"
        >
          {/* Drop Zone */}
          <Card className="overflow-hidden">
            <CardContent className="p-0">
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                className={`
                  relative p-8 text-center transition-all duration-200 cursor-pointer
                  border-2 border-dashed rounded-lg m-4
                  ${isDragging 
                    ? "border-primary bg-primary/5 scale-[1.02]" 
                    : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50"
                  }
                `}
              >
                <input
                  type="file"
                  multiple
                  accept={ACCEPTED_TYPES.join(",")}
                  onChange={handleFileInput}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  disabled={isUploading}
                />
                <div className="space-y-4">
                  <div className={`
                    mx-auto w-16 h-16 rounded-full flex items-center justify-center
                    transition-colors duration-200
                    ${isDragging ? "bg-primary/20" : "bg-muted"}
                  `}>
                    <Upload className={`h-8 w-8 ${isDragging ? "text-primary" : "text-muted-foreground"}`} />
                  </div>
                  <div>
                    <p className="text-lg font-medium">
                      {isDragging ? "Drop files here" : "Drag & drop files here"}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">
                      or click to browse • PDF, DOCX, TXT up to 10MB
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* File List */}
          <AnimatePresence mode="popLayout">
            {files.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
              >
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center justify-between">
                      <span>Selected Files ({files.length})</span>
                      <Badge variant="secondary">{files.reduce((acc, f) => acc + f.file.size, 0) / 1024 / 1024 > 1 
                        ? `${(files.reduce((acc, f) => acc + f.file.size, 0) / 1024 / 1024).toFixed(1)} MB`
                        : `${(files.reduce((acc, f) => acc + f.file.size, 0) / 1024).toFixed(0)} KB`
                      }</Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {files.map((fileProgress) => (
                      <motion.div
                        key={fileProgress.file.name}
                        layout
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        className="flex items-center gap-3 p-3 rounded-lg bg-muted/50"
                      >
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-background">
                          <FileText className="h-5 w-5 text-primary" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{fileProgress.file.name}</p>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <span>{formatFileSize(fileProgress.file.size)}</span>
                            {fileProgress.status === "uploading" && (
                              <>
                                <span>•</span>
                                <span>{fileProgress.progress}%</span>
                              </>
                            )}
                            {fileProgress.status === "processing" && (
                              <>
                                <span>•</span>
                                <span className="text-primary">Processing...</span>
                              </>
                            )}
                            {fileProgress.status === "completed" && (
                              <>
                                <span>•</span>
                                <span className="text-success">Complete</span>
                              </>
                            )}
                          </div>
                          {(fileProgress.status === "uploading" || fileProgress.status === "processing") && (
                            <Progress value={fileProgress.progress} className="h-1 mt-2" />
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {fileProgress.status === "completed" && (
                            <CheckCircle2 className="h-5 w-5 text-success" />
                          )}
                          {fileProgress.status === "processing" && (
                            <Loader2 className="h-5 w-5 text-primary animate-spin" />
                          )}
                          {fileProgress.status === "error" && (
                            <AlertCircle className="h-5 w-5 text-destructive" />
                          )}
                          {!isUploading && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => removeFile(fileProgress.file.name)}
                              className="text-muted-foreground hover:text-destructive transition-colors"
                              title="Remove file"
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Council Visualization */}
          <AnimatePresence>
            {showCouncil && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
              >
                <CouncilVisualization isProcessing={isUploading} />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Settings Panel */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-6"
        >
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Settings className="h-4 w-4" />
                Audit Settings
              </CardTitle>
              <CardDescription>Configure analysis parameters</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="project-name">Project Name</Label>
                <Input
                  id="project-name"
                  placeholder="e.g., SaaS Platform Contract"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  disabled={isUploading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="domain">Domain / Industry</Label>
                <Select value={domain} onValueChange={setDomain} disabled={isUploading}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select domain" />
                  </SelectTrigger>
                  <SelectContent>
                    {domains.map((d) => (
                      <SelectItem key={d} value={d}>{d}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="force-ocr">Force OCR</Label>
                  <p className="text-xs text-muted-foreground">
                    Process scanned documents
                  </p>
                </div>
                <Switch
                  id="force-ocr"
                  checked={forceOcr}
                  onCheckedChange={setForceOcr}
                  disabled={isUploading}
                />
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>Analysis Mode</Label>
                <div className="grid grid-cols-2 gap-2">
                  <Button
                    type="button"
                    variant={analysisMode === "quick" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setAnalysisMode("quick")}
                    disabled={isUploading}
                    className={analysisMode === "quick" ? "bg-gradient-primary" : ""}
                  >
                    Quick Scan
                  </Button>
                  <Button
                    type="button"
                    variant={analysisMode === "deep" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setAnalysisMode("deep")}
                    disabled={isUploading}
                    className={analysisMode === "deep" ? "bg-gradient-primary" : ""}
                  >
                    Deep Analysis
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground">
                  {analysisMode === "quick" 
                    ? "Fast: Get actionable flashcards in ~30 seconds" 
                    : "Thorough: Full tech audit, legal analysis & synthesis (~2 min)"}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-primary/5 border-primary/20">
            <CardContent className="p-4">
              <div className="flex gap-3">
                <Info className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-foreground">How it works</p>
                  <p className="text-muted-foreground mt-1">
                    Our 3-Agent Council (Legal, Business, Finance) will independently analyze your documents, 
                    then debate and cross-reference findings to surface critical gaps.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Button 
            className="w-full bg-gradient-primary hover:opacity-90" 
            size="lg"
            onClick={handleUpload}
            disabled={files.length === 0 || isUploading}
          >
            {isUploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Start Audit Analysis
              </>
            )}
          </Button>
        </motion.div>
      </div>
    </div>
  );
}
