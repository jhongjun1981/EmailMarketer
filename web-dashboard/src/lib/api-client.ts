import type {
  ContactCreate,
  ContactUpdate,
  ContactListResponse,
  ContactResponse,
  ContactBatchImport,
  SegmentCreate,
  SegmentUpdate,
  SegmentResponse,
  TemplateCreate,
  TemplateUpdate,
  TemplateResponse,
  TemplatePreviewResponse,
  CampaignCreate,
  CampaignResponse,
  CampaignStatsResponse,
  EmailLogEntry,
  WorkflowCreate,
  WorkflowResponse,
  WorkflowListItem,
  WorkflowExecutionEntry,
  OverviewReport,
  TrendDataPoint,
  CampaignDetailReport,
  EngagementEntry,
  SmtpAccount,
  SmtpAccountCreate,
  SmtpAccountUpdate,
  HealthResponse,
} from "./api-types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8100";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "changeme-your-secret-key";

class ApiError extends Error {
  status: number;
  data: unknown;
  constructor(status: number, data: unknown) {
    super(`API Error ${status}`);
    this.status = status;
    this.data = data;
  }
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      ...options?.headers,
    },
  });
  if (!res.ok) {
    let data: unknown;
    try {
      data = await res.json();
    } catch {
      data = { error: res.statusText };
    }
    throw new ApiError(res.status, data);
  }
  return res.json();
}

// ── Contacts ──

export function listContacts(params: {
  page?: number;
  page_size?: number;
  status?: string;
  segment_id?: number;
  search?: string;
} = {}) {
  const sp = new URLSearchParams();
  if (params.page) sp.set("page", String(params.page));
  if (params.page_size) sp.set("page_size", String(params.page_size));
  if (params.status) sp.set("status", params.status);
  if (params.segment_id) sp.set("segment_id", String(params.segment_id));
  if (params.search) sp.set("search", params.search);
  return apiFetch<ContactListResponse>(`/api/v1/contacts?${sp}`);
}

export function getContact(id: number) {
  return apiFetch<ContactResponse>(`/api/v1/contacts/${id}`);
}

export function createContact(req: ContactCreate) {
  return apiFetch<ContactResponse>("/api/v1/contacts", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function updateContact(id: number, req: ContactUpdate) {
  return apiFetch<ContactResponse>(`/api/v1/contacts/${id}`, {
    method: "PUT",
    body: JSON.stringify(req),
  });
}

export function deleteContact(id: number) {
  return apiFetch<{ ok: boolean }>(`/api/v1/contacts/${id}`, {
    method: "DELETE",
  });
}

export function batchImportContacts(req: ContactBatchImport) {
  return apiFetch<{ created: number; skipped: number; total: number }>(
    "/api/v1/contacts/batch",
    { method: "POST", body: JSON.stringify(req) }
  );
}

export function addContactToSegment(contactId: number, segmentId: number) {
  return apiFetch<{ ok: boolean }>(
    `/api/v1/contacts/${contactId}/segments/${segmentId}`,
    { method: "POST" }
  );
}

export function removeContactFromSegment(contactId: number, segmentId: number) {
  return apiFetch<{ ok: boolean }>(
    `/api/v1/contacts/${contactId}/segments/${segmentId}`,
    { method: "DELETE" }
  );
}

// ── Segments ──

export function listSegments() {
  return apiFetch<SegmentResponse[]>("/api/v1/segments");
}

export function getSegment(id: number) {
  return apiFetch<SegmentResponse>(`/api/v1/segments/${id}`);
}

export function createSegment(req: SegmentCreate) {
  return apiFetch<SegmentResponse>("/api/v1/segments", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function updateSegment(id: number, req: SegmentUpdate) {
  return apiFetch<SegmentResponse>(`/api/v1/segments/${id}`, {
    method: "PUT",
    body: JSON.stringify(req),
  });
}

export function deleteSegment(id: number) {
  return apiFetch<{ ok: boolean }>(`/api/v1/segments/${id}`, {
    method: "DELETE",
  });
}

export function refreshSegment(id: number) {
  return apiFetch<{ message: string; contact_count: number }>(
    `/api/v1/segments/${id}/refresh`,
    { method: "POST" }
  );
}

export function getSegmentContacts(
  id: number,
  page = 1,
  page_size = 50
) {
  return apiFetch<ContactResponse[]>(
    `/api/v1/segments/${id}/contacts?page=${page}&page_size=${page_size}`
  );
}

// ── Templates ──

export function listTemplates(category?: string) {
  const sp = category ? `?category=${category}` : "";
  return apiFetch<TemplateResponse[]>(`/api/v1/templates${sp}`);
}

export function getTemplate(id: number) {
  return apiFetch<TemplateResponse>(`/api/v1/templates/${id}`);
}

export function createTemplate(req: TemplateCreate) {
  return apiFetch<TemplateResponse>("/api/v1/templates", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function updateTemplate(id: number, req: TemplateUpdate) {
  return apiFetch<TemplateResponse>(`/api/v1/templates/${id}`, {
    method: "PUT",
    body: JSON.stringify(req),
  });
}

export function deleteTemplate(id: number) {
  return apiFetch<{ ok: boolean }>(`/api/v1/templates/${id}`, {
    method: "DELETE",
  });
}

export function previewTemplate(id: number, data: Record<string, string>) {
  return apiFetch<TemplatePreviewResponse>(
    `/api/v1/templates/${id}/preview`,
    { method: "POST", body: JSON.stringify({ data }) }
  );
}

export function testSendTemplate(
  id: number,
  to_email: string,
  data: Record<string, string>
) {
  return apiFetch<{ status: string; message: string }>(
    `/api/v1/templates/${id}/test-send`,
    { method: "POST", body: JSON.stringify({ to_email, data }) }
  );
}

// ── Campaigns ──

export function listCampaigns() {
  return apiFetch<CampaignResponse[]>("/api/v1/campaigns");
}

export function getCampaign(id: number) {
  return apiFetch<CampaignResponse>(`/api/v1/campaigns/${id}`);
}

export function createCampaign(req: CampaignCreate) {
  return apiFetch<CampaignResponse>("/api/v1/campaigns", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function sendCampaign(id: number) {
  return apiFetch<{ message: string; campaign_id: number }>(
    `/api/v1/campaigns/${id}/send`,
    { method: "POST" }
  );
}

export function scheduleCampaign(id: number, scheduled_at: string) {
  return apiFetch<{ message: string; campaign_id: number }>(
    `/api/v1/campaigns/${id}/schedule`,
    { method: "POST", body: JSON.stringify({ scheduled_at }) }
  );
}

export function pauseCampaign(id: number) {
  return apiFetch<{ ok: boolean }>(`/api/v1/campaigns/${id}/pause`, {
    method: "POST",
  });
}

export function cancelCampaign(id: number) {
  return apiFetch<{ ok: boolean }>(`/api/v1/campaigns/${id}/cancel`, {
    method: "POST",
  });
}

export function getCampaignStats(id: number) {
  return apiFetch<CampaignStatsResponse>(
    `/api/v1/campaigns/${id}/stats`
  );
}

export function getCampaignLogs(
  id: number,
  page = 1,
  page_size = 50,
  status?: string
) {
  const sp = new URLSearchParams({
    page: String(page),
    page_size: String(page_size),
  });
  if (status) sp.set("status", status);
  return apiFetch<EmailLogEntry[]>(
    `/api/v1/campaigns/${id}/logs?${sp}`
  );
}

// ── Workflows ──

export function listWorkflows() {
  return apiFetch<WorkflowListItem[]>("/api/v1/workflows");
}

export function getWorkflow(id: number) {
  return apiFetch<WorkflowResponse>(`/api/v1/workflows/${id}`);
}

export function createWorkflow(req: WorkflowCreate) {
  return apiFetch<WorkflowResponse>("/api/v1/workflows", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function activateWorkflow(id: number) {
  return apiFetch<{ ok: boolean; status: string }>(
    `/api/v1/workflows/${id}/activate`,
    { method: "POST" }
  );
}

export function pauseWorkflow(id: number) {
  return apiFetch<{ ok: boolean; status: string }>(
    `/api/v1/workflows/${id}/pause`,
    { method: "POST" }
  );
}

export function deleteWorkflow(id: number) {
  return apiFetch<{ ok: boolean }>(`/api/v1/workflows/${id}`, {
    method: "DELETE",
  });
}

export function getWorkflowExecutions(
  id: number,
  page = 1,
  page_size = 50
) {
  return apiFetch<WorkflowExecutionEntry[]>(
    `/api/v1/workflows/${id}/executions?page=${page}&page_size=${page_size}`
  );
}

// ── Reports ──

export function getOverview() {
  return apiFetch<OverviewReport>("/api/v1/reports/overview");
}

export function getTrends(days = 30) {
  return apiFetch<TrendDataPoint[]>(`/api/v1/reports/trends?days=${days}`);
}

export function getCampaignReport(id: number) {
  return apiFetch<CampaignDetailReport>(`/api/v1/reports/campaigns/${id}`);
}

export function getContactEngagement(limit = 20) {
  return apiFetch<EngagementEntry[]>(
    `/api/v1/reports/contacts/engagement?limit=${limit}`
  );
}

// ── System ──

export function getHealth() {
  return apiFetch<HealthResponse>("/api/v1/system/health");
}

export function listSmtpAccounts() {
  return apiFetch<SmtpAccount[]>("/api/v1/system/smtp/accounts");
}

export function addSmtpAccount(req: SmtpAccountCreate) {
  return apiFetch<SmtpAccount & { message: string }>(
    "/api/v1/system/smtp/accounts",
    { method: "POST", body: JSON.stringify(req) }
  );
}

export function updateSmtpAccount(id: number, req: SmtpAccountUpdate) {
  return apiFetch<SmtpAccount & { message: string }>(
    `/api/v1/system/smtp/accounts/${id}`,
    { method: "PUT", body: JSON.stringify(req) }
  );
}

export function deleteSmtpAccount(id: number) {
  return apiFetch<{ ok: boolean; message: string }>(
    `/api/v1/system/smtp/accounts/${id}`,
    { method: "DELETE" }
  );
}

export function testSmtp(email: string, password: string, to_email: string) {
  return apiFetch<{ status: string; message: string }>(
    "/api/v1/system/smtp/test",
    { method: "POST", body: JSON.stringify({ email, password, to_email }) }
  );
}
