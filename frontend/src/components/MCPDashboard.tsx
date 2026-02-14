/**
 * MCP Dashboard component - displays MCP tools, resources, and prompts
 * Allows users to interact with MCP functionality directly
 */
import { useState, useEffect } from 'react';
import { useMCP } from '../hooks/useMCP';
import {
  MCPTool,
  MCPResource,
  MCPPrompt,
  MCPOrderSummary,
} from '../types/mcp';

export function MCPDashboard() {
  const mcp = useMCP();
  const [tools, setTools] = useState<MCPTool[]>([]);
  const [resources, setResources] = useState<MCPResource[]>([]);
  const [prompts, setPrompts] = useState<MCPPrompt[]>([]);
  const [orders, setOrders] = useState<MCPOrderSummary[]>([]);
  const [activeTab, setActiveTab] = useState<'tools' | 'resources' | 'prompts' | 'orders'>('tools');
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [toolParams, setToolParams] = useState<Record<string, any>>({});
  const [toolResult, setToolResult] = useState<any>(null);
  const [healthStatus, setHealthStatus] = useState<string | null>(null);

  // Load initial data (only once on mount)
  useEffect(() => {
    const loadData = async () => {
      const [toolsData, resourcesData, promptsData, healthData] = await Promise.all([
        mcp.listTools(),
        mcp.listResources(),
        mcp.listPrompts(),
        mcp.checkHealth(),
      ]);

      setTools(toolsData);
      setResources(resourcesData);
      setPrompts(promptsData);
      if (healthData) {
        setHealthStatus(healthData.message);
      }
    };

    loadData();
  }, []); // Empty dependency array = run once on mount

  const handleExecuteTool = async () => {
    if (!selectedTool) return;

    const result = await mcp.executeTool(selectedTool.name, toolParams);
    setToolResult(result);

    // If it was a list_user_orders call, update the orders state
    if (selectedTool.name === 'list_user_orders' && result.result?.success) {
      setOrders(result.result.orders || []);
    }
  };

  const handleListOrders = async () => {
    const result = await mcp.listUserOrders(10);
    if (result.success) {
      setOrders(result.orders || []);
      setToolResult(result);
    } else {
      setToolResult({ error: result.error || 'Failed to list orders' });
    }
  };

  const handleGetOrderDetails = async (orderId: string) => {
    const result = await mcp.getOrderDetails(orderId);
    setToolResult(result);
  };

  const handleRequestCancellation = async (orderId: string) => {
    const result = await mcp.requestOrderCancellation(orderId, 'Testing MCP flow');
    setToolResult(result);
  };

  const updateParam = (key: string, value: any) => {
    setToolParams((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">MCP Dashboard</h2>
        {healthStatus && (
          <div className="text-sm text-gray-600">
            <span className="inline-block w-2 h-2 bg-green-500 rounded-full mr-2"></span>
            {healthStatus}
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 mb-6">
        <button
          onClick={() => setActiveTab('tools')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'tools'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Tools
        </button>
        <button
          onClick={() => setActiveTab('resources')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'resources'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Resources
        </button>
        <button
          onClick={() => setActiveTab('prompts')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'prompts'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Prompts
        </button>
        <button
          onClick={() => setActiveTab('orders')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'orders'
              ? 'border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Orders
        </button>
      </div>

      {/* Tools Tab */}
      {activeTab === 'tools' && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Available MCP Tools ({tools.length})</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {tools.map((tool) => (
              <div
                key={tool.name}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedTool?.name === tool.name
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedTool(tool)}
              >
                <h4 className="font-semibold text-gray-800">{tool.name}</h4>
                <p className="text-sm text-gray-600 mt-1">{tool.description}</p>
                <div className="mt-2">
                  <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                    {Object.keys(tool.parameters).length} parameters
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Tool Execution */}
          {selectedTool && (
            <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
              <h4 className="font-semibold text-lg mb-4">Execute: {selectedTool.name}</h4>

              {Object.entries(selectedTool.parameters).map(([paramName, param]) => (
                <div key={paramName} className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {paramName}
                    {param.required && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  <input
                    type={param.type === 'integer' ? 'number' : 'text'}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder={param.description}
                    value={toolParams[paramName] || ''}
                    onChange={(e) => updateParam(paramName, e.target.value)}
                    required={param.required}
                  />
                  <p className="text-xs text-gray-500 mt-1">{param.description}</p>
                </div>
              ))}

              <button
                onClick={handleExecuteTool}
                disabled={mcp.loading}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {mcp.loading ? 'Executing...' : 'Execute Tool'}
              </button>
            </div>
          )}

          {/* Quick Actions */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-3">
            <button
              onClick={handleListOrders}
              disabled={mcp.loading}
              className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:bg-gray-400"
            >
              List My Orders
            </button>
          </div>

          {/* Tool Result */}
          {toolResult && (
            <div className={`mt-4 p-4 rounded-md ${
              toolResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
              }`}>
              <h5 className="font-semibold mb-2">
                {toolResult.success ? '✓ Success' : '✗ Error'}
              </h5>
              <pre className="text-xs overflow-auto max-h-64 bg-white p-2 rounded">
                {JSON.stringify(toolResult, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Resources Tab */}
      {activeTab === 'resources' && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Available MCP Resources ({resources.length})</h3>

          <div className="space-y-3">
            {resources.map((resource) => (
              <div key={resource.uri} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                <h4 className="font-semibold text-gray-800">{resource.name}</h4>
                <p className="text-sm text-gray-600 mt-1">{resource.description}</p>
                <div className="mt-2 flex items-center justify-between">
                  <code className="text-xs bg-gray-200 px-2 py-1 rounded">{resource.uri}</code>
                  <span className="text-xs text-gray-500">{resource.mime_type}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Prompts Tab */}
      {activeTab === 'prompts' && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Available MCP Prompts ({prompts.length})</h3>

          <div className="space-y-3">
            {prompts.map((prompt) => (
              <div key={prompt.name} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                <h4 className="font-semibold text-gray-800">{prompt.name}</h4>
                <p className="text-sm text-gray-600 mt-1">{prompt.description}</p>
                <div className="mt-2">
                  <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
                    {prompt.arguments.length} arguments
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Orders Tab */}
      {activeTab === 'orders' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">My Orders</h3>
            <button
              onClick={handleListOrders}
              disabled={mcp.loading}
              className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
            >
              {mcp.loading ? 'Loading...' : 'Refresh Orders'}
            </button>
          </div>

          {orders.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No orders found. Click "Refresh Orders" to load your orders.
            </div>
          ) : (
            <div className="space-y-3">
              {orders.map((order) => (
                <div key={order.order_id} className="p-4 border border-gray-200 rounded-lg bg-white hover:border-blue-300">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-semibold text-gray-800">{order.order_id}</h4>
                      <p className="text-sm text-gray-600">{order.customer_name}</p>
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded ${
                      order.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                      order.status === 'shipped' ? 'bg-blue-100 text-blue-800' :
                      order.status === 'delivered' ? 'bg-green-100 text-green-800' :
                      order.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {order.status}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between text-sm">
                    <span className="text-gray-600">{order.item_count} items</span>
                    <span className="font-semibold text-gray-800">${order.total.toFixed(2)}</span>
                  </div>
                  <div className="mt-3 flex gap-2">
                    <button
                      onClick={() => handleGetOrderDetails(order.order_id)}
                      className="flex-1 bg-blue-600 text-white py-2 px-3 rounded-md hover:bg-blue-700 text-sm"
                    >
                      View Details
                    </button>
                    {order.status === 'processing' || order.status === 'shipped' ? (
                      <button
                        onClick={() => handleRequestCancellation(order.order_id)}
                        className="flex-1 bg-red-600 text-white py-2 px-3 rounded-md hover:bg-red-700 text-sm"
                      >
                        Cancel Order
                      </button>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
