import { motion } from "framer-motion";
import { Settings, Sliders, Database, Key, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Separator } from "@/components/ui/separator";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";

export default function SettingsPage() {
  const [ambiguityThreshold, setAmbiguityThreshold] = useState([0.7]);
  const [leverageThreshold, setLeverageThreshold] = useState([0.6]);
  const { toast } = useToast();

  const handleRebuildIndex = () => {
    toast({ title: "Rebuilding index...", description: "This may take a few minutes." });
  };

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1">Configure analysis parameters and API settings.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Sliders className="h-5 w-5" />Analysis Thresholds</CardTitle>
          <CardDescription>Adjust sensitivity for risk detection</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <div className="flex justify-between"><Label>Ambiguity Threshold</Label><span className="text-sm font-medium">{ambiguityThreshold[0].toFixed(2)}</span></div>
            <Slider value={ambiguityThreshold} onValueChange={setAmbiguityThreshold} min={0.5} max={0.95} step={0.05} />
          </div>
          <div className="space-y-3">
            <div className="flex justify-between"><Label>Leverage Threshold</Label><span className="text-sm font-medium">{leverageThreshold[0].toFixed(2)}</span></div>
            <Slider value={leverageThreshold} onValueChange={setLeverageThreshold} min={0.5} max={0.95} step={0.05} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Key className="h-5 w-5" />API Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>API Endpoint</Label>
            <Input defaultValue="https://api.specgap.io/v1" />
          </div>
          <div className="space-y-2">
            <Label>API Key</Label>
            <Input type="password" placeholder="sk-..." />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Database className="h-5 w-5" />Vector Index</CardTitle>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={handleRebuildIndex}><RefreshCw className="h-4 w-4 mr-2" />Rebuild Index</Button>
        </CardContent>
      </Card>
    </motion.div>
  );
}
