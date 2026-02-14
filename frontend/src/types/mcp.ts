/**
 * MCP (Model Context Protocol) types for Kunjal Agents
 */

// MCP Tool types
export interface MCPToolParameter {
  type: string;
  description: string;
  required: boolean;
  default?: any;
}

export interface MCPTool {
  name: string;
  description: string;
  parameters: Record<string, MCPToolParameter>;
}

export interface MCPToolResult {
  success: boolean;
  result?: any;
  error?: string;
}

export interface MCPToolRequest {
  tool_name: string;
  params: Record<string, any>;
}

// MCP Resource types
export interface MCPResource {
  uri: string;
  name: string;
  description: string;
  mime_type: string;
}

export interface MCPResourceData {
  success: boolean;
  data?: string;
  error?: string;
}

// MCP Prompt types
export interface MCPPromptArgument {
  name: string;
  type: string;
  required: boolean;
  description: string;
}

export interface MCPPrompt {
  name: string;
  description: string;
  arguments: MCPPromptArgument[];
}

export interface MCPPromptData {
  success: boolean;
  prompt?: string;
  error?: string;
}

// MCP API Response types
export interface MCPToolsResponse {
  tools: MCPTool[];
}

export interface MCPResourcesResponse {
  resources: MCPResource[];
}

export interface MCPPromptsResponse {
  prompts: MCPPrompt[];
}

export interface MCPHealthResponse {
  status: string;
  message: string;
}

// MCP Order-specific types (from tools)
export interface MCPOrderDetails {
  order_id: string;
  customer_name: string;
  status: string;
  items: string[];
  total: number;
  date: string;
  verification_codes: string[];
}

export interface MCPOrderSummary {
  order_id: string;
  status: string;
  total: number;
  date: string;
  customer_name: string;
  item_count: number;
}

export interface MCPOrdersListResult {
  success: boolean;
  orders: MCPOrderSummary[];
  count: number;
}

export interface MCPOrderDetailsResult {
  success: boolean;
  order: MCPOrderDetails;
}

export interface MCPCancellationRequestResult {
  success: boolean;
  requires_approval: true;
  approval_id: string;
  message: string;
  order_id: string;
}

export interface MCPCancellationConfirmResult {
  success: boolean;
  message: string;
  refund_amount: number;
  order_id: string;
}
