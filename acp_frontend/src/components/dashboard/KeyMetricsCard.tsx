"use client";

import React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription
} from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { LucideIcon } from 'lucide-react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

interface KeyMetricsCardProps {
  title: string;
  value: string;
  icon: LucideIcon;
  description: string;
  trend?: 'improving' | 'declining' | 'neutral';
  trendValue?: string;
  metricUnit?: string;
}

export default function KeyMetricsCard({
  title,
  value,
  icon: Icon,
  description,
  trend,
  trendValue,
  metricUnit
}: KeyMetricsCardProps) {
  let TrendIcon = Minus;
  let trendColor = "text-muted-foreground";

  if (trend === 'improving') {
    TrendIcon = ArrowUpRight;
    trendColor = "text-success";
  } else if (trend === 'declining') {
    TrendIcon = ArrowDownRight;
    trendColor = "text-destructive";
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {value}
          {metricUnit && <span className="text-xs text-muted-foreground ml-1">{metricUnit}</span>}
        </div>
        <p className="text-xs text-muted-foreground pt-1">{description}</p>
        {trend && trendValue && (
          <div className={cn("flex items-center text-xs mt-2", trendColor)}>
            <TrendIcon className={cn("h-3 w-3 mr-1", trendColor)} />
            {trendValue}
          </div>
        )}
      </CardContent>
    </Card>
  );
} 