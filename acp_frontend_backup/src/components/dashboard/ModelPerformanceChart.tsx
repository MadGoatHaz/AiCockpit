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
  RechartsLineChart, // Corrected to LineChart
  CartesianGrid,
  XAxis,
  YAxis,
  Line
} from "@/components/ui/chart"

const chartData = [
  { month: "Jan", modelA_accuracy: 82, modelB_accuracy: 75, modelA_latency: 120, modelB_latency: 150 },
  { month: "Feb", modelA_accuracy: 85, modelB_accuracy: 78, modelA_latency: 115, modelB_latency: 145 },
  { month: "Mar", modelA_accuracy: 88, modelB_accuracy: 80, modelA_latency: 110, modelB_latency: 140 },
  { month: "Apr", modelA_accuracy: 86, modelB_accuracy: 82, modelA_latency: 112, modelB_latency: 138 },
  { month: "May", modelA_accuracy: 90, modelB_accuracy: 85, modelA_latency: 105, modelB_latency: 130 },
  { month: "Jun", modelA_accuracy: 91, modelB_accuracy: 87, modelA_latency: 100, modelB_latency: 125 },
];

const chartConfig = {
  modelA_accuracy: {
    label: "Model A Acc. (%)",
    color: "hsl(var(--primary))",
  },
  modelB_accuracy: {
    label: "Model B Acc. (%)",
    color: "hsl(var(--accent))",
  },
  modelA_latency: {
    label: "Model A Lat. (ms)",
    color: "hsl(var(--primary))", // Can reuse colors or use different ones
    yAxis: "latency", // Specify a different Y-axis
  },
  modelB_latency: {
    label: "Model B Lat. (ms)",
    color: "hsl(var(--accent))",
    yAxis: "latency", // Specify a different Y-axis
  },
} satisfies Record<string, { label: string; color: string; yAxis?: string}>

export default function ModelPerformanceChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Model Performance Trends</CardTitle>
        <CardDescription>Accuracy (%) and Latency (ms) over the last 6 months</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[250px] w-full">
          <RechartsLineChart accessibilityLayer data={chartData}>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="month"
              tickLine={false}
              tickMargin={10}
              axisLine={false}
            />
            <YAxis yAxisId="accuracy" dataKey="modelA_accuracy" unit="%" domain={[0,100]}/>
            <YAxis yAxisId="latency" orientation="right" dataKey="modelA_latency" unit="ms" domain={[0, 'auto']} />
            <ChartTooltip cursor={false} content={<ChartTooltipContent hideIndicator />} />
            <ChartLegend content={<ChartLegendContent />} />
            <Line
              dataKey="modelA_accuracy"
              type="monotone"
              stroke="var(--color-modelA_accuracy)"
              strokeWidth={2}
              dot={false}
              yAxisId="accuracy"
            />
            <Line
              dataKey="modelB_accuracy"
              type="monotone"
              stroke="var(--color-modelB_accuracy)"
              strokeWidth={2}
              dot={false}
              yAxisId="accuracy"
            />
             <Line
              dataKey="modelA_latency"
              type="monotone"
              stroke="var(--color-modelA_latency)"
              strokeWidth={2}
              strokeDasharray="3 3"
              dot={true}
              yAxisId="latency"
            />
            <Line
              dataKey="modelB_latency"
              type="monotone"
              stroke="var(--color-modelB_latency)"
              strokeWidth={2}
              strokeDasharray="3 3"
              dot={true}
              yAxisId="latency"
            />
          </RechartsLineChart>
        </ChartContainer>
      </CardContent>
      <CardFooter className="flex-col items-start gap-2 text-sm">
        <div className="leading-none text-muted-foreground">
          Showing data for two mock models over the past 6 months.
        </div>
      </CardFooter>
    </Card>
  )
} 