class VClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async registerModule(path, force = false, mcpConfigs = null) {
    const [modulePath, className] = path.split(':');
    
    // Prepare form data
    const formData = new FormData();
    formData.append('force', force.toString().toLowerCase());
    
    if (mcpConfigs) {
      formData.append('mcp_configs', JSON.stringify(mcpConfigs));
    }

    // Note: In browser environment, we can't directly serialize Python objects
    // This would need to be handled differently in a real implementation
    // For now, we'll just send the module path
    formData.append('module_path', path);

    try {
      const response = await fetch(`${this.baseUrl}/api/modules`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
        body: formData
      });

      if (response.ok) {
        console.log('Module registered successfully.');
        return await response.json();
      } else {
        const errorText = await response.text();
        throw new Error(`Failed to register module. Status: ${response.status}, Response: ${errorText}`);
      }
    } catch (error) {
      console.error('Error registering module:', error);
      throw error;
    }
  }

  async callResponseHandler(requestData) {
    const shouldStream = requestData.stream || false;
    console.log(`[VClient] Making request to ${this.baseUrl}/v1/responses with stream=${shouldStream}`);

    try {
      const response = await fetch(`${this.baseUrl}/v1/responses`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to call response_handler. Status: ${response.status}, Response: ${errorText}`);
      }

      if (shouldStream) {
        // Handle streaming response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let chunksProcessed = 0;

        try {
          while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            chunksProcessed++;
            if (value) {
              try {
                const text = decoder.decode(value, { stream: true });
                console.log(text);
                // Here you would typically emit an event or call a callback with the chunk
                return {
                  type: 'stream',
                  data: text
                };
              } catch (e) {
                console.error('Error decoding chunk:', e);
              }
            }
          }
        } catch (e) {
          console.error('Error during streaming:', e);
        } finally {
          console.log(`Finished streaming. Total chunks processed: ${chunksProcessed}`);
        }
      } else {
        // Handle non-streaming response
        const data = await response.json();
        console.log('Non-streaming response received successfully:', data);
        return {
          type: 'json',
          data
        };
      }
    } catch (error) {
      console.error('Error in callResponseHandler:', error);
      throw error;
    }
  }
}

export default VClient; 