"use client";

import React from 'react';
import KeyMetricsCard from '@/components/dashboard/KeyMetricsCard';
import SystemHealthChart from '@/components/dashboard/SystemHealthChart';
import ModelPerformanceChart from '@/components/dashboard/ModelPerformanceChart';
import {
  Users,
  Cpu,
  MemoryStick,
  AlertTriangle,
  ListChecks,
  Timer
} from 'lucide-react';

// Placeholder for chart components which will be created later
// import SystemHealthChart from '@/components/dashboard/SystemHealthChart';
// import ModelPerformanceChart from '@/components/dashboard/ModelPerformanceChart';

export default function DashboardPage() {
  // Mock data for demonstration
  const metrics = [
    {
      title: "Active AI Agents",
      value: "12",
      icon: Users,
      description: "Currently operational AI agents.",
      trend: "improving" as const,
      trendValue: "+2 since last hour"
    },
    {
      title: "CPU Utilization",
      value: "72",
      metricUnit: "%",
      icon: Cpu,
      description: "Overall system CPU load.",
      trend: "declining" as const,
      trendValue: "+8% from average"
    },
    {
      title: "Memory Usage",
      value: "64",
      metricUnit: "%",
      icon: MemoryStick,
      description: "Total memory consumed by services.",
      trend: "neutral" as const,
      trendValue: "Stable"
    },
    {
      title: "Critical Alerts",
      value: "3",
      icon: AlertTriangle,
      description: "Immediate attention required.",
      trend: "declining" as const,
      trendValue: "+1 new alert"
    },
    {
      title: "Processed Tasks",
      value: "1,280",
      icon: ListChecks,
      description: "Tasks completed in the last 24h.",
      trend: "improving" as const,
      trendValue: "+15% vs yesterday"
    },
    {
      title: "Avg. Model Latency",
      value: "120",
      metricUnit: "ms",
      icon: Timer,
      description: "Average AI model response time.",
      trend: "improving" as const,
      trendValue: "-12ms from last week"
    }
  ];

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold">Dashboard (AiSight)</h1>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-3">
        {metrics.map((metric) => (
          <KeyMetricsCard
            key={metric.title}
            title={metric.title}
            value={metric.value}
            icon={metric.icon}
            description={metric.description}
            trend={metric.trend}
            trendValue={metric.trendValue}
            metricUnit={metric.metricUnit}
          />
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5 mt-2">
        <div className="lg:col-span-3">
          <SystemHealthChart />
        </div>
        <div className="lg:col-span-2">
          <ModelPerformanceChart />
        </div>
      </div>
    </div>
  );
} 