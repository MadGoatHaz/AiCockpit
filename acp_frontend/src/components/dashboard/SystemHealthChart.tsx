"use client"

import * as React from "react"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  RechartsBarChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Bar
} from "@/components/ui/chart"

const chartData = [
  { date: "2024-07-01", health: 92 },
  { date: "2024-07-02", health: 95 },
  { date: "2024-07-03", health: 88 },
  { date: "2024-07-04", health: 93 },
  { date: "2024-07-05", health: 90 },
  { date: "2024-07-06", health: 96 },
  { date: "2024-07-07", health: 94 },
];

const chartConfig = {
  health: {
    label: "System Health",
    color: "hsl(var(--primary))", // Use a theme color
  },
} satisfies Record<string, { label: string; color: string }>

export default function SystemHealthChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>System Health Over Time</CardTitle>
        <CardDescription>Percentage of system components operating nominally (last 7 days)</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[250px] w-full">
          <RechartsBarChart accessibilityLayer data={chartData}>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="date"
              tickLine={false}
              tickMargin={10}
              axisLine={false}
              tickFormatter={(value: string) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            />
            <YAxis domain={[Math.min(...chartData.map(d => d.health)) - 5, 100]} unit="%" />
            <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
            <ChartLegend content={<ChartLegendContent />} />
            <Bar dataKey="health" fill="var(--color-health)" radius={4} />
          </RechartsBarChart>
        </ChartContainer>
      </CardContent>
      <CardFooter className="flex-col items-start gap-2 text-sm">
        <div className="flex gap-2 font-medium leading-none">
          Trending up for 3 days <ArrowUpRight className="h-4 w-4 text-success" />
        </div>
        <div className="leading-none text-muted-foreground">
          Showing data for the last 7 days
        </div>
      </CardFooter>
    </Card>
  )
}

// Dummy ArrowUpRight for footer until lucide-react is fully available or if we want to minimize imports
const ArrowUpRight = ({ className }: { className?: string }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className={className} width="1em" height="1em">
    <path d="M5 17.59L15.59 7H9V5h10v10h-2V8.41L6.41 19 5 17.59z"/>
  </svg>
); 