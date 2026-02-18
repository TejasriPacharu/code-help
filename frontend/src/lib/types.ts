// Agent types
export interface Agent {
  name: string;
  description: string;
  handoffs: string[];
  tools: string[];
  input_guardrails: string[];
}

// Context types
export interface CopilotContext {
  project_name?: string;
  repo_path?: string;
  current_file?: string;
  language?: string;
  framework?: string;
  error_message?: string;
  stack_trace?: string;
  error_type?: string;
  affected_endpoint?: string;
  diagnosis_report?: string;
  code_smells?: string[];
  refactoring_suggestions?: RefactoringSuggestion[];
  complexity_score?: number;
  test_coverage?: number;
  test_framework?: string;
  generated_tests?: GeneratedTest[];
  load_test_config?: Record<string, string>;
  vulnerabilities?: Vulnerability[];
  security_score?: number;
  rate_limit_config?: Record<string, string>;
  dependency_audit?: DependencyAudit[];
  documentation_type?: string;
  generated_docs?: string;
}

export interface RefactoringSuggestion {
  pattern: string;
  description: string;
  benefit: string;
  effort: string;
}

export interface GeneratedTest {
  type: string;
  content: string;
}

export interface Vulnerability {
  id: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  type: string;
  description: string;
  affected_files: string[];
  recommendation: string;
}

export interface DependencyAudit {
  package: string;
  version: string;
  severity: string;
  vulnerability: string;
  description: string;
  fixed_in: string;
}

// Event types
export interface AgentEvent {
  id: string;
  type: 'message' | 'handoff' | 'tool_call' | 'tool_output' | 'context_update';
  agent: string;
  content: string;
  metadata?: Record<string, any>;
  timestamp?: number;
}

// Guardrail types
export interface GuardrailCheck {
  id: string;
  name: string;
  input: string;
  reasoning: string;
  passed: boolean;
  timestamp: number;
}

// Server state types
export interface ServerState {
  thread_id: string;
  current_agent: string;
  context: CopilotContext;
  agents: Agent[];
  events: AgentEvent[];
  guardrails: GuardrailCheck[];
  events_delta?: AgentEvent[];
}

// Message types
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  agent?: string;
}

// Chat thread types
export interface Thread {
  id: string;
  created_at: string;
  title?: string;
}

// API response types
export interface BootstrapResponse {
  thread_id: string;
  current_agent: string;
  context: CopilotContext;
  agents: Agent[];
  events: AgentEvent[];
  guardrails: GuardrailCheck[];
}
