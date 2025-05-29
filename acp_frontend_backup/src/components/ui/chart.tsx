"use client"

import * as React from "react"
import { Label, Pie, PieChart as RechartsPieChart, Sector, Cell, Bar, BarChart as RechartsBarChart, Line, LineChart as RechartsLineChart, CartesianGrid, XAxis, YAxis, Tooltip as RechartsTooltip, Legend as RechartsLegend, ResponsiveContainer } from "recharts"

import {
   dezelfdePassProps,
  useGetColors,
  resolveProps,
} from "@/lib/chart-utils" // Placeholder for actual chart utilities from shadcn/ui or custom
import { cn } from "@/lib/utils"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip" // Re-using existing tooltip

// ChartContainer
interface ChartContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  config?: Record<string, any>; // Simplified config type
  children: React.ReactNode;
}
const ChartContainer = React.forwardRef<HTMLDivElement, ChartContainerProps>(
  ({ children, className, config, ...props }, ref) => {
    return (
      <div ref={ref} className={cn("w-full h-[300px]", className)} {...props}>
        <ResponsiveContainer width="100%" height="100%">
          {children}
        </ResponsiveContainer>
      </div>
    )
  }
)
ChartContainer.displayName = "ChartContainer"

// ChartTooltip & Content (Basic structure, can be enhanced)
const ChartTooltipContext = React.createContext<{
  active?: boolean
  payload?: any[]
  label?: string | number
} | null>(null)

const ChartTooltip = ({ active, payload, label }: any) => {
  const contextValue = React.useMemo(() => ({ active, payload, label }), [
    active,
    payload,
    label,
  ])

  if (!active || !payload || payload.length === 0) {
    return null
  }

  return (
    <ChartTooltipContext.Provider value={contextValue}>
      <ChartTooltipContent />
    </ChartTooltipContext.Provider>
  )
}
ChartTooltip.displayName = "ChartTooltip"

const ChartTooltipContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { hideLabel?: boolean; hideIndicator?: boolean }
>(({ className, hideLabel, hideIndicator, ...props }, ref) => {
  const context = React.useContext(ChartTooltipContext)

  if (!context || !context.active) {
    return null
  }

  const { payload, label } = context

  return (
    <div
      ref={ref}
      className={cn(
        "grid items-start gap-1.5 rounded-lg border bg-background px-2.5 py-1.5 text-xs shadow-xl animate-in fade-in-0",
        className
      )}
      {...props}
    >
      {!hideLabel && label && (
        <div className="font-medium">{label.toString()}</div>
      )}
      {payload?.map((item, index) => (
        <div key={index} className="grid grid-cols-[auto,1fr,auto] items-center gap-1.5">
          {!hideIndicator && item.color && (
            <div
              className="h-2.5 w-2.5 shrink-0 rounded-[2px] border-[--color-border] bg-[--color-bg]"
              style={{
                '--color-bg': item.color,
                '--color-border': item.color,
              } as React.CSSProperties}
            />
          )}
          <div className={cn("flex flex-wrap items-baseline gap-x-1.5")}>
            <span className="font-medium text-muted-foreground">
              {item.name}
            </span>
            <span className="font-medium text-foreground">
              {item.value}
            </span>
            {item.unit && (
              <span className="text-xs text-muted-foreground">
                {item.unit}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
})
ChartTooltipContent.displayName = "ChartTooltipContent"

// ChartLegend & Content (Basic structure)
const ChartLegendContext = React.createContext<{
  payload?: any[]
} | null>(null)

const ChartLegend = ({ payload, ...props }: any) => {
  const contextValue = React.useMemo(() => ({ payload }), [payload])
  if (!payload || !payload.length) {
    return null
  }

  return (
    <ChartLegendContext.Provider value={contextValue}>
      <ChartLegendContent {...props} />
    </ChartLegendContext.Provider>
  )
}
ChartLegend.displayName = "ChartLegend"

const ChartLegendContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { nameKey?: string; hideIcon?: boolean }
>(({ className, nameKey = "name", hideIcon, ...props }, ref) => {
  const context = React.useContext(ChartLegendContext)

  if (!context || !context.payload) {
    return null
  }

  return (
    <div
      ref={ref}
      className={cn("flex items-center justify-center gap-4", className)}
      {...props}
    >
      {context.payload.map((item, index) => (
        <div
          key={index}
          className={cn(
            "flex items-center gap-1.5 [&>svg]:h-3 [&>svg]:w-3 [&>svg]:text-muted-foreground"
          )}
        >
          {!hideIcon && item.color && (
             <div
              className="h-2 w-2.5 shrink-0 rounded-[2px] bg-[--color-payload]"
              style={{
                '--color-payload': item.color,
              } as React.CSSProperties}
            />
          )}
          {item[nameKey] || item.dataKey}
        </div>
      ))}
    </div>
  )
})
ChartLegendContent.displayName = "ChartLegendContent"

// Export necessary recharts components and custom ones
export {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  // Recharts exports
  RechartsPieChart,
  RechartsBarChart,
  RechartsLineChart,
  CartesianGrid,
  XAxis,
  YAxis,
  RechartsTooltip, // Exporting the Recharts Tooltip as well, can be used directly
  RechartsLegend, // Exporting the Recharts Legend as well
  ResponsiveContainer,
  Pie,
  Cell,
  Bar,
  Line,
  Label,
  Sector
} 