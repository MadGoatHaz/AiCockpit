"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"; // Assuming Card is a ShadCN component
import { Cpu, MemoryStick, AlertTriangle, Thermometer, Zap } from 'lucide-react'; // Example icons
import { cn } from '@/lib/utils';

interface PersistentInfoWidgetsProps {
  showCpu: boolean;
  showMemory: boolean;
  showGpuMemory: boolean;
  showGpuUsage: boolean;
  showCriticalAlerts: boolean;
}

const WidgetCard = ({ title, icon: Icon, value, visible }: { title: string; icon: React.ElementType; value: string; visible: boolean }) => {
  if (!visible) return null;
  return (
    <Card className="w-[180px] bg-background/80 backdrop-blur-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-xs font-medium">{title}</CardTitle>
        <Icon className="h-3 w-3 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-lg font-bold">{value}</div>
      </CardContent>
    </Card>
  );
};

export default function PersistentInfoWidgets({ 
  showCpu,
  showMemory,
  showGpuMemory,
  showGpuUsage,
  showCriticalAlerts 
}: PersistentInfoWidgetsProps) {
  // In a real app, these values would come from a global state or API
  const mockData = {
    cpu: "72%",
    memory: "12.3 GB",
    gpuMemory: "4.1 GB",
    gpuUsage: "35%",
    criticalAlerts: "3"
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-2">
      <WidgetCard title="CPU Usage" icon={Cpu} value={mockData.cpu} visible={showCpu} />
      <WidgetCard title="Memory Usage" icon={MemoryStick} value={mockData.memory} visible={showMemory} />
      <WidgetCard title="GPU Memory" icon={Zap} value={mockData.gpuMemory} visible={showGpuMemory} /> 
      <WidgetCard title="GPU Usage" icon={Thermometer} value={mockData.gpuUsage} visible={showGpuUsage} />
      <WidgetCard title="Critical Alerts" icon={AlertTriangle} value={mockData.criticalAlerts} visible={showCriticalAlerts} />
    </div>
  );
}
