import { configureGenkit } from '@genkit-ai/core';
import { googleAI } from '@genkit-ai/google-ai'; // Example, adjust if using a different provider

export default configureGenkit({
  plugins: [
    googleAI(), // Example, replace with actual plugins used
  ],
  logLevel: 'debug',
  enableTracingAndMetrics: true,
}); 