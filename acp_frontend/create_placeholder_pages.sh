#!/bin/bash

# Script to create placeholder page.tsx files for various app sections
# Run this script from within the acp_frontend directory.

# Base app directory
APP_DIR="src/app/(app)"

# Ensure the base app directory exists
if [ ! -d "$APP_DIR" ]; then
  echo "Error: Base app directory '$APP_DIR' not found."
  echo "Please ensure you have run the previous structure creation script or created it manually."
  echo "Run this script from within the acp_frontend directory."
  exit 1
fi

echo "Creating placeholder page files..."

# --- aisight ---
AISIGHT_PAGE="$APP_DIR/aisight/page.tsx"
mkdir -p "$(dirname "$AISIGHT_PAGE")"
cat > "$AISIGHT_PAGE" << EOL
// $AISIGHT_PAGE
export default function AiSightPage() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">AiSight Page</h1>
      <p>Metrics and charts will go here.</p>
    </div>
  );
}
EOL
echo "Created $AISIGHT_PAGE"

# --- logs ---
LOGS_PAGE="$APP_DIR/logs/page.tsx"
mkdir -p "$(dirname "$LOGS_PAGE")"
cat > "$LOGS_PAGE" << EOL
// $LOGS_PAGE
export default function LogsPage() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">Logs Page</h1>
      <p>Log streaming and summarization tools will go here.</p>
    </div>
  );
}
EOL
echo "Created $LOGS_PAGE"

# --- alerts ---
ALERTS_PAGE="$APP_DIR/alerts/page.tsx"
mkdir -p "$(dirname "$ALERTS_PAGE")"
cat > "$ALERTS_PAGE" << EOL
// $ALERTS_PAGE
export default function AlertsPage() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">Alerts Page</h1>
      <p>Alert configuration and display will go here.</p>
    </div>
  );
}
EOL
echo "Created $ALERTS_PAGE"

# --- history ---
HISTORY_PAGE="$APP_DIR/history/page.tsx"
mkdir -p "$(dirname "$HISTORY_PAGE")"
cat > "$HISTORY_PAGE" << EOL
// $HISTORY_PAGE
export default function HistoryPage() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">History Page</h1>
      <p>Historical performance data and charts will go here.</p>
    </div>
  );
}
EOL
echo "Created $HISTORY_PAGE"

# --- fleet ---
FLEET_PAGE="$APP_DIR/fleet/page.tsx"
mkdir -p "$(dirname "$FLEET_PAGE")"
cat > "$FLEET_PAGE" << EOL
// $FLEET_PAGE
export default function FleetPage() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">Fleet Page</h1>
      <p>Fleet status grid and agent cards will go here.</p>
    </div>
  );
}
EOL
echo "Created $FLEET_PAGE"

# --- live-preview ---
LIVE_PREVIEW_PAGE="$APP_DIR/live-preview/page.tsx"
mkdir -p "$(dirname "$LIVE_PREVIEW_PAGE")"
cat > "$LIVE_PREVIEW_PAGE" << EOL
// $LIVE_PREVIEW_PAGE
export default function LivePreviewPage() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold">Live Preview Page</h1>
      <p>This area is for a live instance of the selected workspace (conceptual).</p>
    </div>
  );
}
EOL
echo "Created $LIVE_PREVIEW_PAGE"

echo "Placeholder page creation complete."
