"use client";

import React, { useEffect, useState, useCallback } from 'react';
import { CogIcon, CheckCircle2, AlertTriangleIcon, Loader2 } from 'lucide-react'; // Or any other relevant icon
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export interface AIModelConfigurationPanelProps {
  workspaceId?: string; // Optional, might be useful for context
  // Add any other props needed for configuration, e.g., current model, available models
  onConfigurationChange?: (config: { selectedModelId?: string, temperature?: number }) => void;
}

interface AIModelSessionConfigData {
  selected_model_id?: string | null; // Allow null from backend if not set
  temperature?: number | null; // Allow null from backend if not set
  // custom_parameters?: Record<string, any>; // For future use
}

interface LLMConfigFromBackend {
    model_id: string;
    model_name: string;
    // backend_type: string; // Could be useful for display
    // parameters: Record<string, any>; // For more detailed info
}

interface DiscoveredLLMConfigResponse {
    configs: LLMConfigFromBackend[];
}

const DEFAULT_MODEL_ID = "gemma2-latest"; // A sensible default
const DEFAULT_TEMPERATURE = 0.7;

const AIModelConfigurationPanel: React.FC<AIModelConfigurationPanelProps> = ({ workspaceId, onConfigurationChange }) => {
  const [selectedModel, setSelectedModel] = useState<string>(DEFAULT_MODEL_ID);
  const [temperature, setTemperature] = useState<number>(DEFAULT_TEMPERATURE);
  const [availableModels, setAvailableModels] = useState<LLMConfigFromBackend[]>([]);
  const [isLoading, setIsLoading] = useState(false); // Covers both config and model list loading initially
  const [isModelsLoading, setIsModelsLoading] = useState(false); // Separate state for models list refresh
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchAvailableModels = useCallback(async () => {
    setIsModelsLoading(true);
    setModelsError(null);
    try {
        const response = await fetch('/api/llm/models'); // Assuming /api/llm/models is the endpoint
        if (!response.ok) {
            const errData = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(errData.detail || "Failed to load available AI models");
        }
        const data: DiscoveredLLMConfigResponse = await response.json();
        setAvailableModels(data.configs || []);
        if (data.configs && data.configs.length > 0 && !data.configs.find(m => m.model_id === selectedModel)) {
            // If current selectedModel is not in the new list, try to select the first one from the list
            // This could happen if the previously saved model is no longer available.
            // However, fetchConfig already sets selectedModel, so this might only be for initial load or if models change drastically.
        }
    } catch (err) {
        console.error("Error fetching available models:", err);
        setModelsError(err instanceof Error ? err.message : String(err));
        setAvailableModels([]); // Clear models on error
    } finally {
        setIsModelsLoading(false);
    }
  }, []); // Removed selectedModel from dependencies as it might cause loop if model list changes it

  const fetchConfig = useCallback(async () => {
    if (!workspaceId) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/sessions/${workspaceId}/ai_config`);
      if (!response.ok) {
        const errData = await response.json().catch(() => ({detail: response.statusText}));
        throw new Error(errData.detail || "Failed to load AI configuration");
      }
      const config: AIModelSessionConfigData = await response.json();
      setSelectedModel(config.selected_model_id || DEFAULT_MODEL_ID);
      setTemperature(config.temperature ?? DEFAULT_TEMPERATURE); // Use ?? for null/undefined to default
      if (onConfigurationChange) {
        onConfigurationChange({ 
          selectedModelId: config.selected_model_id || DEFAULT_MODEL_ID, 
          temperature: config.temperature ?? DEFAULT_TEMPERATURE 
        });
      }
    } catch (err) {
      console.error("Error fetching AI config:", err);
      setError(err instanceof Error ? err.message : String(err));
      // Keep current/default values on error
    } finally {
      setIsLoading(false);
    }
  }, [workspaceId, onConfigurationChange]);

  useEffect(() => {
    fetchConfig();
    fetchAvailableModels(); // Fetch models on initial load too
  }, [fetchConfig, fetchAvailableModels]);

  const handleSaveConfiguration = async () => {
    if (!workspaceId) {
      setError("Workspace ID is missing. Cannot save configuration.");
      return;
    }
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    const configToSave: AIModelSessionConfigData = {
      selected_model_id: selectedModel,
      temperature: temperature,
    };

    try {
      const response = await fetch(`/api/sessions/${workspaceId}/ai_config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configToSave),
      });
      if (!response.ok) {
        const errData = await response.json().catch(() => ({detail: response.statusText}));
        throw new Error(errData.detail || "Failed to save AI configuration");
      }
      const savedConfig: AIModelSessionConfigData = await response.json();
      setSelectedModel(savedConfig.selected_model_id || DEFAULT_MODEL_ID);
      setTemperature(savedConfig.temperature ?? DEFAULT_TEMPERATURE);
      setSuccessMessage("Configuration saved successfully!");
      if (onConfigurationChange) {
        onConfigurationChange({ 
          selectedModelId: savedConfig.selected_model_id || DEFAULT_MODEL_ID, 
          temperature: savedConfig.temperature ?? DEFAULT_TEMPERATURE 
        });
      }
      setTimeout(() => setSuccessMessage(null), 3000); // Clear success message after 3s
    } catch (err) {
      console.error("Error saving AI config:", err);
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-center">
          <CogIcon className="h-5 w-5 mr-2 text-primary" />
          <CardTitle className="text-lg">AI Model Configuration</CardTitle>
        </div>
        <CardDescription className="text-xs">
          Configure the AI model and related settings for this workspace ({workspaceId ? workspaceId.substring(0,8) + '...' : 'N/A'}).
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-grow space-y-6 overflow-auto p-4">
        {isLoading && (
          <div className="flex items-center justify-center text-muted-foreground py-4">
            <Loader2 className="h-5 w-5 animate-spin mr-2" /> Loading configuration...
          </div>
        )}
        {!isLoading && error && ( // Show error only if not loading, to prevent flicker
          <div className="flex items-center p-3 rounded-md bg-destructive/10 text-destructive text-xs">
            <AlertTriangleIcon className="h-4 w-4 mr-2 flex-shrink-0"/>
            <div><span className="font-semibold">Error:</span> {error} <Button variant="link" size="sm" className="p-0 h-auto text-xs ml-1" onClick={fetchConfig}>Retry</Button></div>
          </div>
        )}
        {!isLoading && ( // Don't show form if initial load is happening or failed critically (error state might show retry)
          <>
            <div className="space-y-2">
              <Label htmlFor="ai-model-select" className="text-xs">Select AI Model</Label>
              {isModelsLoading && <p className="text-xs text-muted-foreground"><Loader2 className="h-3 w-3 animate-spin inline mr-1"/>Loading models...</p>}
              {modelsError && <p className="text-xs text-destructive"><AlertTriangleIcon className="h-3 w-3 inline mr-1"/>Models error: {modelsError} <Button variant="link" size="sm" className="p-0 h-auto text-xs" onClick={fetchAvailableModels}>Retry</Button></p>}
              <Select value={selectedModel} onValueChange={setSelectedModel} disabled={isSaving || isLoading || isModelsLoading || availableModels.length === 0}>
                <SelectTrigger id="ai-model-select" className="text-xs">
                  <SelectValue placeholder="Choose a model" />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.length === 0 && !isModelsLoading && (
                    <SelectItem value="no-models" disabled className="text-xs text-muted-foreground">No models available or failed to load.</SelectItem>
                  )}
                  {availableModels.map(model => (
                    <SelectItem key={model.model_id} value={model.model_id} className="text-xs">
                      {model.model_name} ({model.model_id})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="temperature" className="text-xs">Temperature: {temperature.toFixed(1)}</Label>
              <div className="flex items-center space-x-2">
                <span className="text-[11px] text-muted-foreground">Precise</span>
                <input 
                  type="range" 
                  id="temperature" 
                  min="0" 
                  max="2" // Max temperature often 2.0
                  step="0.1" 
                  value={temperature} 
                  onChange={(e) => setTemperature(parseFloat(e.target.value))} 
                  className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
                  disabled={isSaving || isLoading}
                />
                <span className="text-[11px] text-muted-foreground">Creative</span>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Controls randomness. Lower values (e.g., 0.2) are more focused, higher values (e.g., 1.0+) are more creative.
              </p>
            </div>
          </>
        )}
      </CardContent>
      <CardFooter className="border-t pt-4 flex flex-col items-start space-y-2">
        <Button onClick={handleSaveConfiguration} size="sm" className="text-xs" disabled={isSaving || isLoading}>
          {isSaving ? <><Loader2 className="h-4 w-4 animate-spin mr-1.5" />Saving...</> : "Save Configuration"}
        </Button>
        {successMessage && (
          <div className="flex items-center text-green-600 text-xs mt-2">
            <CheckCircle2 className="h-4 w-4 mr-1.5"/> {successMessage}
          </div>
        )}
        {/* Error during save is shown near form or as a global notification ideally */}
      </CardFooter>
    </Card>
  );
};

export default AIModelConfigurationPanel; 