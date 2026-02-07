import { useState } from "react";
import { motion } from "framer-motion";
import { Copy, Mail, FileText, Check, Edit3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";

interface RedlineEditorProps {
  redlineContent: string;
  emailDraft: string;
}

export function RedlineEditor({ redlineContent, emailDraft }: RedlineEditorProps) {
  const [editedRedline, setEditedRedline] = useState(redlineContent);
  const [editedEmail, setEditedEmail] = useState(emailDraft);
  const [copied, setCopied] = useState<string | null>(null);
  const { toast } = useToast();

  const handleCopy = async (content: string, type: string) => {
    await navigator.clipboard.writeText(content);
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
    toast({
      title: "Copied to clipboard",
      description: `${type} content copied successfully.`,
    });
  };

  const renderRedlineWithHighlights = (content: string) => {
    const lines = content.split("\n");
    return lines.map((line, index) => {
      if (line.startsWith("PROPOSED CHANGE:")) {
        return (
          <div key={index} className="bg-success/10 border-l-4 border-success px-3 py-1 my-2">
            <span className="text-success font-medium">{line}</span>
          </div>
        );
      }
      if (line.startsWith("RATIONALE:")) {
        return (
          <div key={index} className="bg-primary/10 border-l-4 border-primary px-3 py-1 my-2">
            <span className="text-primary font-medium">{line}</span>
          </div>
        );
      }
      if (line.includes('"Unlimited Storage"')) {
        return (
          <p key={index} className="my-1">
            {line.split('"Unlimited Storage"').map((part, i, arr) => (
              <span key={i}>
                {part}
                {i < arr.length - 1 && (
                  <span className="bg-destructive/20 text-destructive line-through px-1">
                    "Unlimited Storage"
                  </span>
                )}
              </span>
            ))}
          </p>
        );
      }
      if (line.includes("500GB")) {
        return (
          <p key={index} className="my-1">
            {line.split("500GB").map((part, i, arr) => (
              <span key={i}>
                {part}
                {i < arr.length - 1 && (
                  <span className="bg-success/20 text-success font-medium px-1">
                    500GB
                  </span>
                )}
              </span>
            ))}
          </p>
        );
      }
      return <p key={index} className="my-1">{line}</p>;
    });
  };

  return (
    <div className="space-y-6">
      <Tabs defaultValue="redline" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="redline" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Redline Document
          </TabsTrigger>
          <TabsTrigger value="email" className="flex items-center gap-2">
            <Mail className="h-4 w-4" />
            Email Draft
          </TabsTrigger>
        </TabsList>

        <TabsContent value="redline" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg">Proposed Contract Amendments</CardTitle>
                <CardDescription>Review and edit suggested changes before sending</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="secondary">3 changes</Badge>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleCopy(editedRedline, "Redline")}
                >
                  {copied === "Redline" ? (
                    <Check className="h-4 w-4 mr-1" />
                  ) : (
                    <Copy className="h-4 w-4 mr-1" />
                  )}
                  Copy
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 lg:grid-cols-2">
                {/* Formatted View */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                    <FileText className="h-4 w-4" />
                    Preview
                  </div>
                  <div className="p-4 rounded-lg bg-muted/30 border text-sm font-mono min-h-[300px] overflow-auto">
                    {renderRedlineWithHighlights(editedRedline)}
                  </div>
                  <div className="flex gap-2 text-xs">
                    <div className="flex items-center gap-1">
                      <div className="h-3 w-3 rounded bg-destructive/20" />
                      <span className="text-muted-foreground">Removed</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="h-3 w-3 rounded bg-success/20" />
                      <span className="text-muted-foreground">Added</span>
                    </div>
                  </div>
                </div>

                {/* Edit View */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                    <Edit3 className="h-4 w-4" />
                    Edit
                  </div>
                  <Textarea
                    value={editedRedline}
                    onChange={(e) => setEditedRedline(e.target.value)}
                    className="min-h-[300px] font-mono text-sm"
                    placeholder="Edit the redline content..."
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="email" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg">Negotiation Email</CardTitle>
                <CardDescription>Customizable email template for client communication</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => handleCopy(editedEmail, "Email")}
                >
                  {copied === "Email" ? (
                    <Check className="h-4 w-4 mr-1" />
                  ) : (
                    <Copy className="h-4 w-4 mr-1" />
                  )}
                  Copy
                </Button>
                <Button size="sm">
                  <Mail className="h-4 w-4 mr-1" />
                  Open in Email
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Textarea
                value={editedEmail}
                onChange={(e) => setEditedEmail(e.target.value)}
                className="min-h-[400px] font-mono text-sm"
                placeholder="Compose your email..."
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
