#!/bin/bash

# Script to create the initial directory and file structure for acp_frontend/src
# Run this script from within the acp_frontend directory.

# Base source directory
SRC_DIR="src"

# Ensure the src directory exists
if [ ! -d "$SRC_DIR" ]; then
  echo "Error: src directory not found. Please run this script from within the acp_frontend directory that contains src."
  exit 1
fi

echo "Creating directory structure and placeholder files in $SRC_DIR..."

# --- app ---
mkdir -p "$SRC_DIR/app/(app)/interact"
touch "$SRC_DIR/app/(app)/interact/page.tsx"

mkdir -p "$SRC_DIR/app/(app)/aisight"
touch "$SRC_DIR/app/(app)/aisight/page.tsx"

mkdir -p "$SRC_DIR/app/(app)/logs"
touch "$SRC_DIR/app/(app)/logs/page.tsx"

mkdir -p "$SRC_DIR/app/(app)/alerts"
touch "$SRC_DIR/app/(app)/alerts/page.tsx"

mkdir -p "$SRC_DIR/app/(app)/history"
touch "$SRC_DIR/app/(app)/history/page.tsx"

mkdir -p "$SRC_DIR/app/(app)/fleet"
touch "$SRC_DIR/app/(app)/fleet/page.tsx"

mkdir -p "$SRC_DIR/app/(app)/live-preview"
touch "$SRC_DIR/app/(app)/live-preview/page.tsx"

touch "$SRC_DIR/app/(app)/layout.tsx"
# Note: src/app/favicon.ico, globals.css, layout.tsx (root), page.tsx (root)
# are typically created by create-next-app. This script won't touch them
# unless they were deleted.

# --- components ---
mkdir -p "$SRC_DIR/components/ui" # For ShadCN
mkdir -p "$SRC_DIR/components/layout"
touch "$SRC_DIR/components/layout/AppSidebar.tsx"
touch "$SRC_DIR/components/layout/HeaderBar.tsx"
touch "$SRC_DIR/components/layout/PersistentInfoWidgets.tsx"

mkdir -p "$SRC_DIR/components/workspaces"
touch "$SRC_DIR/components/workspaces/WorkspacesPage.tsx"
touch "$SRC_DIR/components/workspaces/FileBrowserPanel.tsx"
touch "$SRC_DIR/components/workspaces/AIChatPanel.tsx"
touch "$SRC_DIR/components/workspaces/FileViewerPanel.tsx"
touch "$SRC_DIR/components/workspaces/WorkspaceSettingsPanel.tsx"
touch "$SRC_DIR/components/workspaces/AIModelAndParametersPanel.tsx"
touch "$SRC_DIR/components/workspaces/TerminalManagerPanel.tsx"

mkdir -p "$SRC_DIR/components/aisight"
touch "$SRC_DIR/components/aisight/KeyMetricsCard.tsx"
touch "$SRC_DIR/components/aisight/SystemHealthChart.tsx"
touch "$SRC_DIR/components/aisight/ModelPerformanceChart.tsx"

mkdir -p "$SRC_DIR/components/logs"
touch "$SRC_DIR/components/logs/LogStreamView.tsx"
touch "$SRC_DIR/components/logs/LogSummarizer.tsx"

mkdir -p "$SRC_DIR/components/alerts"
touch "$SRC_DIR/components/alerts/AlertsTable.tsx"
touch "$SRC_DIR/components/alerts/CreateAlertModal.tsx"

mkdir -p "$SRC_DIR/components/history"
touch "$SRC_DIR/components/history/HistoricalDataChart.tsx"

mkdir -p "$SRC_DIR/components/fleet"
touch "$SRC_DIR/components/fleet/FleetStatusGrid.tsx"
touch "$SRC_DIR/components/fleet/AgentCard.tsx"

mkdir -p "$SRC_DIR/components/shared"
touch "$SRC_DIR/components/shared/CustomIcon.tsx" # Example
touch "$SRC_DIR/components/shared/LoadingSpinner.tsx" # Example

# --- lib ---
mkdir -p "$SRC_DIR/lib"
# utils.ts is created by shadcn-ui init
touch "$SRC_DIR/lib/constants.ts"
touch "$SRC_DIR/lib/types.ts"
touch "$SRC_DIR/lib/api.ts"

# --- hooks ---
mkdir -p "$SRC_DIR/hooks"
touch "$SRC_DIR/hooks/useToast.ts" # Example from your doc
touch "$SRC_DIR/hooks/useMobile.ts" # Example from your doc

# --- contexts ---
mkdir -p "$SRC_DIR/contexts"
touch "$SRC_DIR/contexts/ThemeProvider.tsx" # Example
touch "$SRC_DIR/contexts/AuthProvider.tsx" # Example

echo "Structure creation complete."
echo "Please ensure files like src/app/globals.css, src/app/layout.tsx (root), src/app/page.tsx (root), and src/lib/utils.ts exist from create-next-app and shadcn-ui init."
echo "You will now need to populate these .tsx and .ts files with placeholder or actual component code."
