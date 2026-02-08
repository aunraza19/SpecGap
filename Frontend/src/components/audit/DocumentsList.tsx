import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { FileText, Download, Eye, FileType } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { AuditDocument } from "@/types/api";

interface DocumentsListProps {
  documents: AuditDocument[];
  auditId: string;
}

const fileTypeConfig = {
  pdf: { color: "bg-red-500/10 text-red-600", label: "PDF" },
  docx: { color: "bg-blue-500/10 text-blue-600", label: "DOCX" },
  txt: { color: "bg-gray-500/10 text-gray-600", label: "TXT" },
};

export function DocumentsList({ documents, auditId }: DocumentsListProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Uploaded Documents</h3>
        <Badge variant="secondary">{documents.length} files</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {documents.map((doc, index) => {
          const fileType = fileTypeConfig[doc.file_type] || fileTypeConfig.txt;
          
          return (
            <motion.div
              key={doc.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="group hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${fileType.color}`}>
                      <FileText className="h-6 w-6" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate" title={doc.filename}>
                        {doc.filename}
                      </p>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                        <Badge variant="outline" className="text-xs">{fileType.label}</Badge>
                        <span>{doc.page_count} pages</span>
                        <span>•</span>
                        <span>{formatFileSize(doc.size_bytes)}</span>
                      </div>
                      {doc.ocr_processed && (
                        <Badge variant="secondary" className="mt-2 text-xs">
                          OCR Processed
                        </Badge>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 mt-4 pt-4 border-t">
                    <Button variant="outline" size="sm" className="flex-1" asChild>
                      <Link to={`/audits/${auditId}/documents/${encodeURIComponent(doc.filename)}`}>
                        <Eye className="h-4 w-4 mr-1" />
                        View
                      </Link>
                    </Button>
                    <Button variant="ghost" size="icon">
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
