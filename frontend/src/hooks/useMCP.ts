/**
 * MCP (Model Context Protocol) hook for Kunjal Agents
 * Provides functions to interact with MCP tools, resources, and prompts
 */
import { useState, useCallback } from 'react';
import {
  MCPTool,
  MCPToolRequest,
  MCPToolResult,
  MCPResource,
  MCPResourcesResponse,
  MCPPrompt,
  MCPPromptData,
  MCPHealthResponse,
  MCPOrdersListResult,
  MCPOrderDetailsResult,
  MCPCancellationRequestResult,
  MCPCancellationConfirmResult,
} from '../types/mcp';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function useMCP() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Helper function to get auth headers
  const getHeaders = () => {
    const token = localStorage.getItem('token');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  };

  /**
   * List all available MCP tools
   */
  const listTools = useCallback(async (): Promise<MCPTool[]> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/mcp/tools`, {
        method: 'GET',
        headers: getHeaders(),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: MCPToolsResponse = await response.json();
      return data.tools || [];
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Error listing MCP tools:', err);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Execute an MCP tool
   */
  const executeTool = useCallback(async (toolName: string, params: Record<string, any>): Promise<MCPToolResult> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/mcp/tools/execute`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          tool_name: toolName,
          params,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: MCPToolResult = await response.json();
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Error executing MCP tool:', err);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * List all available MCP resources
   */
  const listResources = useCallback(async (): Promise<MCPResource[]> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/mcp/resources`, {
        method: 'GET',
        headers: getHeaders(),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: MCPResourcesResponse = await response.json();
      return data.resources || [];
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Error listing MCP resources:', err);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get a specific MCP resource by URI
   */
  const getResource = useCallback(async (uri: string): Promise<string> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/mcp/resources/${encodeURIComponent(uri)}`, {
        method: 'GET',
        headers: getHeaders(),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data.data || '';
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Error getting MCP resource:', err);
      return '';
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * List all available MCP prompts
   */
  const listPrompts = useCallback(async (): Promise<MCPPrompt[]> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/mcp/prompts`, {
        method: 'GET',
        headers: getHeaders(),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: MCPPromptsResponse = await response.json();
      return data.prompts || [];
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Error listing MCP prompts:', err);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Get a specific MCP prompt by name with parameters
   */
  const getPrompt = useCallback(async (promptName: string, params: Record<string, any>): Promise<MCPPromptData> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/mcp/prompts/${promptName}`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: MCPPromptData = await response.json();
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      console.error('Error getting MCP prompt:', err);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Check MCP health status
   */
  const checkHealth = useCallback(async (): Promise<MCPHealthResponse | null> => {
    try {
      const response = await fetch(`${API_URL}/api/mcp/health`, {
        method: 'GET',
        headers: getHeaders(),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: MCPHealthResponse = await response.json();
      return data;
    } catch (err) {
      console.error('Error checking MCP health:', err);
      return null;
    }
  }, []);

  /**
   * Convenience function: List user orders
   */
  const listUserOrders = useCallback(async (limit: number = 10, statusFilter?: string): Promise<MCPOrdersListResult> => {
    const params: Record<string, any> = { limit };
    if (statusFilter) {
      params.status_filter = statusFilter;
    }

    return await executeTool('list_user_orders', params) as Promise<MCPOrdersListResult>;
  }, [executeTool]);

  /**
   * Convenience function: Get order details
   */
  const getOrderDetails = useCallback(async (orderId: string): Promise<MCPOrderDetailsResult> => {
    return await executeTool('get_order_details', { order_id: orderId }) as Promise<MCPOrderDetailsResult>;
  }, [executeTool]);

  /**
   * Convenience function: Request order cancellation
   */
  const requestOrderCancellation = useCallback(async (orderId: string, reason?: string): Promise<MCPCancellationRequestResult> => {
    const params: Record<string, string> = { order_id: orderId };
    if (reason) {
      params.reason = reason;
    }

    return await executeTool('request_order_cancellation', params) as Promise<MCPCancellationRequestResult>;
  }, [executeTool]);

  /**
   * Convenience function: Confirm order cancellation
   */
  const confirmCancellation = useCallback(async (approvalId: string, verificationCode: string): Promise<MCPCancellationConfirmResult> => {
    return await executeTool('confirm_cancellation', {
      approval_id: approvalId,
      verification_code: verificationCode,
    }) as Promise<MCPCancellationConfirmResult>;
  }, [executeTool]);

  return {
    // State
    loading,
    error,

    // Tool functions
    listTools,
    executeTool,
    listResources,
    getResource,
    listPrompts,
    getPrompt,
    checkHealth,

    // Convenience functions
    listUserOrders,
    getOrderDetails,
    requestOrderCancellation,
    confirmCancellation,
  };
}
