// ── Enums ──
export type ContactStatus = "active" | "unsubscribed" | "bounced" | "complained";
export type CampaignStatus = "draft" | "scheduled" | "sending" | "sent" | "paused" | "cancelled";
export type EmailLogStatus = "queued" | "sending" | "sent" | "delivered" | "opened" | "clicked" | "bounced" | "failed";
export type WorkflowStatus = "active" | "paused" | "draft";
export type TriggerType = "contact_added" | "email_opened" | "link_clicked" | "date_field" | "manual";
export type ActionType = "send_email" | "wait" | "condition" | "add_to_segment" | "remove_from_segment" | "update_contact";

// ── Contact ──
export interface ContactCreate {
  email: string;
  name?: string;
  company?: string;
  phone?: string;
  custom_fields?: Record<string, string>;
  source?: string;
}

export interface ContactUpdate {
  name?: string;
  company?: string;
  phone?: string;
  status?: string;
  custom_fields?: Record<string, string>;
}

export interface ContactResponse {
  id: number;
  email: string;
  name: string;
  company: string;
  phone: string;
  status: ContactStatus;
  custom_fields: Record<string, string>;
  source: string;
  created_at: string;
  updated_at: string;
}

export interface ContactListResponse {
  items: ContactResponse[];
  total: number;
  page: number;
  page_size: number;
}

export interface ContactBatchImport {
  contacts: ContactCreate[];
  segment_id?: number;
}

// ── Segment ──
export interface SegmentCreate {
  name: string;
  description?: string;
  is_dynamic?: boolean;
  rules?: Record<string, unknown>;
}

export interface SegmentUpdate {
  name?: string;
  description?: string;
  rules?: Record<string, unknown>;
}

export interface SegmentResponse {
  id: number;
  name: string;
  description: string;
  is_dynamic: boolean;
  rules?: Record<string, unknown>;
  contact_count: number;
  created_at: string;
}

// ── Template ──
export interface TemplateCreate {
  name: string;
  subject: string;
  html_body: string;
  text_body?: string;
  variables?: string[];
  category?: string;
}

export interface TemplateUpdate {
  name?: string;
  subject?: string;
  html_body?: string;
  text_body?: string;
  variables?: string[];
  category?: string;
}

export interface TemplateResponse {
  id: number;
  name: string;
  subject: string;
  html_body: string;
  text_body: string;
  variables: string[];
  category: string;
  created_at: string;
}

export interface TemplatePreviewResponse {
  subject: string;
  html: string;
  variables_used: string[];
}

// ── Campaign ──
export interface CampaignCreate {
  name: string;
  template_id: number;
  segment_id?: number;
  sender_email: string;
  sender_name?: string;
  reply_to?: string;
  rate_limit?: number;
}

export interface CampaignResponse {
  id: number;
  name: string;
  template_id: number;
  segment_id?: number;
  sender_email: string;
  sender_name: string;
  status: CampaignStatus;
  scheduled_at?: string;
  started_at?: string;
  completed_at?: string;
  total_recipients: number;
  sent_count: number;
  open_count: number;
  click_count: number;
  bounce_count: number;
  unsubscribe_count: number;
  rate_limit: number;
  created_at: string;
}

export interface CampaignStatsResponse {
  campaign_id: number;
  name: string;
  status: string;
  total: number;
  sent: number;
  opened: number;
  clicked: number;
  bounced: number;
  unsubscribed: number;
  open_rate: number;
  click_rate: number;
  bounce_rate: number;
}

export interface EmailLogEntry {
  id: number;
  contact_id: number;
  email: string;
  status: string;
  sent_at?: string;
  opened_at?: string;
  open_count: number;
  click_count: number;
  error?: string;
}

// ── Workflow ──
export interface WorkflowStepData {
  action_type: string;
  config: Record<string, unknown>;
}

export interface WorkflowCreate {
  name: string;
  description?: string;
  trigger_type: string;
  trigger_config?: Record<string, unknown>;
  steps?: WorkflowStepData[];
}

export interface WorkflowResponse {
  id: number;
  name: string;
  description: string;
  status: WorkflowStatus;
  trigger_type: string;
  trigger_config: Record<string, unknown>;
  steps: Array<{ order: number; action_type: string; config: Record<string, unknown> }>;
  created_at: string;
}

export interface WorkflowListItem {
  id: number;
  name: string;
  status: WorkflowStatus;
  trigger_type: string;
  created_at: string;
}

export interface WorkflowExecutionEntry {
  id: number;
  contact_id: number;
  status: string;
  current_step_id?: number;
  started_at?: string;
  completed_at?: string;
  log: unknown[];
}

// ── Reports ──
export interface OverviewReport {
  total_contacts: number;
  active_contacts: number;
  total_campaigns: number;
  total_sent: number;
  total_opened: number;
  total_clicked: number;
  avg_open_rate: number;
  avg_click_rate: number;
}

export interface TrendDataPoint {
  date: string;
  sent: number;
  opened: number;
  clicked: number;
}

export interface CampaignDetailReport {
  campaign_id: number;
  name: string;
  status: string;
  total_recipients: number;
  sent: number;
  opened: number;
  clicked: number;
  bounced: number;
  unsubscribed: number;
  open_rate: number;
  click_rate: number;
  bounce_rate: number;
  status_distribution: Record<string, number>;
  started_at?: string;
  completed_at?: string;
}

export interface EngagementEntry {
  contact_id: number;
  email: string;
  name: string;
  total_emails: number;
  total_opens: number;
  total_clicks: number;
}

// ── SMTP ──
export interface SmtpAccount {
  id: number;
  name: string;
  email: string;
  smtp_host: string;
  smtp_port: number;
  use_ssl: boolean;
  daily_limit: number;
  sent_today: number;
  is_active: boolean;
}

export interface SmtpAccountCreate {
  name: string;
  email: string;
  password: string;
  smtp_host?: string;
  smtp_port?: number;
  use_ssl?: boolean;
  daily_limit?: number;
}

export interface SmtpAccountUpdate {
  name?: string;
  email?: string;
  password?: string;
  smtp_host?: string;
  smtp_port?: number;
  use_ssl?: boolean;
  daily_limit?: number;
  is_active?: boolean;
}

// ── System ──
export interface HealthResponse {
  status: string;
  service: string;
}
