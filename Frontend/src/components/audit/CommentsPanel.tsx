import { useState } from "react";
import { motion } from "framer-motion";
import { MessageSquare, Send, CheckCircle2, User } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import type { Comment, Finding } from "@/types/api";

interface CommentsPanelProps {
  auditId: string;
  findings: Finding[];
}

// Mock comments
const mockComments: Comment[] = [
  {
    id: "com_001",
    finding_id: "find_001",
    audit_id: "aud_001",
    text: "Discussed with legal team - they agree we need to cap storage at 500GB. Client has been notified.",
    author: "John Doe",
    created_at: "2024-01-15T14:30:00Z",
    resolved: false,
  },
  {
    id: "com_002",
    finding_id: "find_003",
    audit_id: "aud_001",
    text: "Finance confirmed the $2.4M exposure calculation. Recommending we add a 12-month cap.",
    author: "Jane Smith",
    created_at: "2024-01-15T15:45:00Z",
    resolved: true,
  },
];

export function CommentsPanel({ auditId, findings }: CommentsPanelProps) {
  const [comments, setComments] = useState<Comment[]>(mockComments);
  const [newComment, setNewComment] = useState("");
  const [selectedFinding, setSelectedFinding] = useState<string>("general");
  const { toast } = useToast();

  const handleSubmit = () => {
    if (!newComment.trim()) return;

    const comment: Comment = {
      id: `com_${Date.now()}`,
      finding_id: selectedFinding === "general" ? undefined : selectedFinding,
      audit_id: auditId,
      text: newComment,
      author: "Current User",
      created_at: new Date().toISOString(),
      resolved: false,
    };

    setComments([comment, ...comments]);
    setNewComment("");
    toast({
      title: "Comment added",
      description: "Your comment has been saved.",
    });
  };

  const handleResolve = (commentId: string) => {
    setComments(comments.map((c) => 
      c.id === commentId ? { ...c, resolved: true } : c
    ));
    toast({
      title: "Comment resolved",
      description: "The comment has been marked as resolved.",
    });
  };

  const getFindingTitle = (findingId?: string) => {
    if (!findingId) return "General";
    const finding = findings.find((f) => f.id === findingId);
    return finding?.title || "Unknown Finding";
  };

  return (
    <div className="space-y-6">
      {/* Add Comment */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Add Comment
          </CardTitle>
          <CardDescription>
            Leave notes, decisions, or action items for your team
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Select value={selectedFinding} onValueChange={setSelectedFinding}>
              <SelectTrigger>
                <SelectValue placeholder="Link to finding (optional)" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="general">General Comment</SelectItem>
                {findings.map((finding) => (
                  <SelectItem key={finding.id} value={finding.id}>
                    {finding.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          <Textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Write your comment..."
            className="min-h-[100px]"
          />
          
          <div className="flex justify-end">
            <Button onClick={handleSubmit} disabled={!newComment.trim()}>
              <Send className="h-4 w-4 mr-2" />
              Post Comment
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Comments List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Comments ({comments.length})</h3>
          <div className="flex gap-2">
            <Badge variant="secondary">{comments.filter((c) => !c.resolved).length} open</Badge>
            <Badge variant="outline">{comments.filter((c) => c.resolved).length} resolved</Badge>
          </div>
        </div>

        {comments.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="p-8 text-center">
              <MessageSquare className="h-12 w-12 mx-auto text-muted-foreground/50" />
              <p className="text-muted-foreground mt-4">No comments yet. Be the first to add one!</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {comments.map((comment, index) => (
              <motion.div
                key={comment.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card className={comment.resolved ? "opacity-60" : ""}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 flex-1">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
                          <User className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium text-sm">{comment.author}</span>
                            <span className="text-xs text-muted-foreground">
                              {new Date(comment.created_at).toLocaleString()}
                            </span>
                            {comment.finding_id && (
                              <Badge variant="outline" className="text-xs">
                                {getFindingTitle(comment.finding_id)}
                              </Badge>
                            )}
                            {comment.resolved && (
                              <Badge variant="secondary" className="text-xs bg-success/10 text-success">
                                <CheckCircle2 className="h-3 w-3 mr-1" />
                                Resolved
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm mt-2">{comment.text}</p>
                        </div>
                      </div>
                      {!comment.resolved && (
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => handleResolve(comment.id)}
                        >
                          <CheckCircle2 className="h-4 w-4 mr-1" />
                          Resolve
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
