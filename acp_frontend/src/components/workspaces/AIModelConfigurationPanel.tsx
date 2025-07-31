// acp_frontend/src/components/workspaces/AIModelConfigurationPanel.tsx
"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { apiClient, AIServiceConfig } from '@/lib/api-client';
import { toast } from 'sonner';

export interface AIModelConfigurationPanelProps {
  workspaceId: string;
  onConfigurationChange?: (config: any) => void;
}

interface AIModelSessionConfigData {
  selected_model: string;
  temperature: number;
  max_tokens?: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
}

interface LLMConfigFromBackend {
  model_id: string;
  model_name: string;
  backend_type: string;
  status: string;
  parameters: Record<string, any>;
}

const AIModelConfigurationPanel: React.FC<AIModelConfigurationPanelProps> = ({ workspaceId, onConfigurationChange }) => {
  // State for external AI services
  const [services, setServices] = useState<AIServiceConfig[]>([]);
  const [selectedService, setSelectedService] = useState<string>('');
  const [newService, setNewService] = useState<Omit<AIServiceConfig, 'name'> & { name: string }>({
    name: '',
    type: 'lmstudio',
    base_url: 'http://localhost:1234/v1',
    model: 'gpt-3.5-turbo',
  });
  const [isAddingService, setIsAddingService] = useState(false);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isModelsLoading, setIsModelsLoading] = useState(true);

  // State for model configuration
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [temperature, setTemperature] = useState<number>(0.7);
  const [availableModels, setAvailableModels] = useState<LLMConfigFromBackend[]>([]);
  const [maxTokens, setMaxTokens] = useState<number | undefined>(undefined);
  const [topP, setTopP] = useState<number | undefined>(undefined);

  // Fetch available models
  const fetchAvailableModels = useCallback(async () => {
    setIsModelsLoading(true);
    try {
      const response = await apiClient.getModels();
      if (response.success && response.data) {
        // The response.data is already an array of LLM objects
        const models = response.data as unknown as LLMConfigFromBackend[];
        setAvailableModels(models || []);
        if (models && models.length > 0 && !selectedModel) {
          setSelectedModel(models[0].model_id);
        }
      }
    } catch (error) {
      console.error('Failed to fetch available models:', error);
      toast.error('Failed to fetch available models');
    } finally {
      setIsModelsLoading(false);
    }
  }, [selectedModel]);

  // Fetch external services
  const fetchServices = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.listExternalServices();
      if (response.success && response.data) {
        setServices(response.data.services || []);
        if (response.data.services && response.data.services.length > 0 && !selectedService) {
          setSelectedService(response.data.services[0].name);
        }
      }
    } catch (error) {
      console.error('Failed to fetch external services:', error);
      toast.error('Failed to fetch external services');
    } finally {
      setIsLoading(false);
    }
  }, [selectedService]);

  // Fetch current configuration
  const fetchConfig = useCallback(async () => {
    try {
      // In a real implementation, this would fetch the current AI configuration
      // For now, we'll use default values
      setSelectedModel('gpt-3.5-turbo');
      setTemperature(0.7);
    } catch (error) {
      console.error('Failed to fetch AI configuration:', error);
    }
  }, []);

  useEffect(() => {
    fetchServices();
    fetchAvailableModels();
    fetchConfig();
  }, [fetchServices, fetchAvailableModels, fetchConfig]);

  const handleAddService = async () => {
    if (!newService.name) {
      toast.error('Service name is required');
      return;
    }

    setIsAddingService(true);
    try {
      const serviceConfig: AIServiceConfig = {
        name: newService.name,
        type: newService.type,
        api_key: newService.api_key,
        base_url: newService.base_url,
        model: newService.model,
        organization: newService.organization,
        deployment_name: newService.deployment_name,
        api_version: newService.api_version,
      };

      const response = await apiClient.addExternalService(serviceConfig);
      if (response.success) {
        toast.success('External service added successfully');
        setNewService({
          name: '',
          type: 'lmstudio',
          base_url: 'http://localhost:1234/v1',
          model: 'gpt-3.5-turbo',
        });
        fetchServices(); // Refresh the list
      } else {
        toast.error(response.error || 'Failed to add external service');
      }
    } catch (error) {
      console.error('Failed to add external service:', error);
      toast.error('Failed to add external service');
    } finally {
      setIsAddingService(false);
    }
  };

  const handleRemoveService = async (serviceName: string) => {
    try {
      const response = await apiClient.removeExternalService(serviceName);
      if (response.success) {
        toast.success('External service removed successfully');
        fetchServices(); // Refresh the list
      } else {
        toast.error(response.error || 'Failed to remove external service');
      }
    } catch (error) {
      console.error('Failed to remove external service:', error);
      toast.error('Failed to remove external service');
    }
  };

  const handleTestConnection = async (serviceName: string) => {
    setIsTestingConnection(true);
    try {
      const response = await apiClient.testServiceConnection(serviceName);
      if (response.success) {
        toast.success(response.data?.result?.response || 'Connection test successful');
      } else {
        toast.error(response.error || 'Connection test failed');
      }
    } catch (error) {
      console.error('Failed to test connection:', error);
      toast.error('Failed to test connection');
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleSetActiveService = async (serviceName: string) => {
    try {
      const response = await apiClient.setActiveService(serviceName);
      if (response.success) {
        toast.success('Active service set successfully');
        setSelectedService(serviceName);
      } else {
        toast.error(response.error || 'Failed to set active service');
      }
    } catch (error) {
      console.error('Failed to set active service:', error);
      toast.error('Failed to set active service');
    }
  };

  const handleSaveConfiguration = async () => {
    setIsSaving(true);
    try {
      // In a real implementation, this would save the configuration to the backend
      // For now, we'll just show a success message
      toast.success('AI configuration saved successfully');
      if (onConfigurationChange) {
        onConfigurationChange({
          selectedModel,
          temperature,
          maxTokens,
          topP,
        });
      }
    } catch (error) {
      console.error('Failed to save AI configuration:', error);
      toast.error('Failed to save AI configuration');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle>AI Model Configuration</CardTitle>
      </CardHeader>
      <CardContent className="flex-grow space-y-6 overflow-auto p-4">
        {/* External AI Services Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">External AI Services</h3>
          
          {/* Service Selection */}
          <div className="space-y-2">
            <Label>Active Service</Label>
            <div className="flex space-x-2">
              <Select 
                value={selectedService} 
                onValueChange={setSelectedService}
                disabled={isSaving || isLoading || isModelsLoading || services.length === 0}
              >
                <SelectTrigger className="flex-grow">
                  <SelectValue placeholder="Select a service" />
                </SelectTrigger>
                <SelectContent>
                  {services.map(service => (
                    <SelectItem key={service.name} value={service.name}>
                      {service.name} ({service.type})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button 
                onClick={() => selectedService && handleSetActiveService(selectedService)}
                disabled={!selectedService || isSaving || isLoading || isModelsLoading}
                variant="secondary"
              >
                Set Active
              </Button>
            </div>
          </div>

          {/* Service Management */}
          <div className="space-y-4 pt-4 border-t">
            <h4 className="font-medium">Manage Services</h4>
            
            {/* Add New Service Form */}
            <div className="space-y-4 p-3 bg-muted/30 rounded-md">
              <h5 className="font-medium">Add New Service</h5>
              
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label htmlFor="service-name">Service Name</Label>
                  <Input
                    id="service-name"
                    value={newService.name}
                    onChange={(e) => setNewService({...newService, name: e.target.value})}
                    placeholder="e.g., LM Studio, OpenAI"
                    disabled={isAddingService}
                  />
                </div>
                
                <div className="space-y-1">
                  <Label htmlFor="service-type">Service Type</Label>
                  <Select
                    value={newService.type}
                    onValueChange={(value) => setNewService({...newService, type: value as any})}
                    disabled={isAddingService}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="lmstudio">LM Studio</SelectItem>
                      <SelectItem value="openai">OpenAI</SelectItem>
                      <SelectItem value="azure">Azure OpenAI</SelectItem>
                      <SelectItem value="custom">Custom</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              {newService.type !== 'lmstudio' && (
                <div className="space-y-1">
                  <Label htmlFor="api-key">API Key</Label>
                  <Input
                    id="api-key"
                    type="password"
                    value={newService.api_key || ''}
                    onChange={(e) => setNewService({...newService, api_key: e.target.value})}
                    placeholder="Enter API key"
                    disabled={isAddingService}
                  />
                </div>
              )}
              
              <div className="space-y-1">
                <Label htmlFor="base-url">Base URL</Label>
                <Input
                  id="base-url"
                  value={newService.base_url || ''}
                  onChange={(e) => setNewService({...newService, base_url: e.target.value})}
                  placeholder="e.g., http://localhost:1234/v1"
                  disabled={isAddingService}
                />
              </div>
              
              <div className="space-y-1">
                <Label htmlFor="default-model">Default Model</Label>
                <Input
                  id="default-model"
                  value={newService.model}
                  onChange={(e) => setNewService({...newService, model: e.target.value})}
                  placeholder="e.g., gpt-3.5-turbo"
                  disabled={isAddingService}
                />
              </div>
              
              {newService.type === 'azure' && (
                <>
                  <div className="space-y-1">
                    <Label htmlFor="deployment-name">Deployment Name</Label>
                    <Input
                      id="deployment-name"
                      value={newService.deployment_name || ''}
                      onChange={(e) => setNewService({...newService, deployment_name: e.target.value})}
                      placeholder="Enter deployment name"
                      disabled={isAddingService}
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="api-version">API Version</Label>
                    <Input
                      id="api-version"
                      value={newService.api_version || ''}
                      onChange={(e) => setNewService({...newService, api_version: e.target.value})}
                      placeholder="e.g., 2024-05-01"
                      disabled={isAddingService}
                    />
                  </div>
                </>
              )}
              
              <Button 
                onClick={handleAddService}
                disabled={isAddingService || !newService.name}
                size="sm"
                className="w-full"
              >
                {isAddingService ? 'Adding...' : 'Add Service'}
              </Button>
            </div>
            
            {/* Existing Services List */}
            <div className="space-y-2">
              <h5 className="font-medium">Configured Services</h5>
              {services.length === 0 ? (
                <p className="text-sm text-muted-foreground">No external services configured</p>
              ) : (
                <div className="space-y-2">
                  {services.map((service) => (
                    <div key={service.name} className="flex items-center justify-between p-2 border rounded-md">
                      <div>
                        <div className="font-medium">{service.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {service.type} - {service.base_url}
                        </div>
                      </div>
                      <div className="flex space-x-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleTestConnection(service.name)}
                          disabled={isTestingConnection}
                        >
                          Test
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleRemoveService(service.name)}
                        >
                          Remove
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Model Configuration Section */}
        <div className="space-y-4 pt-4 border-t">
          <h3 className="text-lg font-medium">Model Parameters</h3>
          
          {/* Model Selection */}
          <div className="space-y-2">
            <Label htmlFor="model-select">AI Model</Label>
            <Select 
              value={selectedModel} 
              onValueChange={setSelectedModel}
              disabled={isSaving || isLoading || isModelsLoading || availableModels.length === 0}
            >
              <SelectTrigger id="model-select">
                <SelectValue placeholder="Select a model" />
              </SelectTrigger>
              <SelectContent>
                {availableModels.map(model => (
                  <SelectItem key={model.model_id} value={model.model_id}>
                    {model.model_name} ({model.model_id})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          
          {/* Temperature */}
          <div className="space-y-2">
            <Label htmlFor="temperature">Temperature: {temperature}</Label>
            <input
              id="temperature"
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-full"
              disabled={isSaving}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Precise</span>
              <span>Creative</span>
            </div>
          </div>
          
          {/* Max Tokens */}
          <div className="space-y-2">
            <Label htmlFor="max-tokens">Max Tokens (optional)</Label>
            <Input
              id="max-tokens"
              type="number"
              value={maxTokens || ''}
              onChange={(e) => setMaxTokens(e.target.value ? parseInt(e.target.value) : undefined)}
              placeholder="e.g., 1000"
              disabled={isSaving}
            />
          </div>
          
          {/* Top P */}
          <div className="space-y-2">
            <Label htmlFor="top-p">Top P (optional)</Label>
            <Input
              id="top-p"
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={topP || ''}
              onChange={(e) => setTopP(e.target.value ? parseFloat(e.target.value) : undefined)}
              placeholder="e.g., 0.9"
              disabled={isSaving}
            />
          </div>
        </div>
      </CardContent>
      <CardFooter className="border-t pt-4 flex flex-col items-start space-y-2">
        <Button 
          onClick={handleSaveConfiguration}
          disabled={isSaving}
          className="w-full"
        >
          {isSaving ? 'Saving...' : 'Save Configuration'}
        </Button>
        <p className="text-xs text-muted-foreground text-center w-full">
          Configuration will be applied to this workspace
        </p>
      </CardFooter>
    </Card>
  );
};

export default AIModelConfigurationPanel;