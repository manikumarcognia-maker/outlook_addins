import { apiGet, apiPost, apiUpload } from "./apiClient";
import type { IndexedDocument, SearchPreviewResult, UploadResult } from "../types";

export async function getSupportedTypes(): Promise<string[]> {
  return apiGet<string[]>("/api/admin/documents/supported-types");
}

export async function uploadDocument(file: File): Promise<UploadResult> {
  const formData = new FormData();
  formData.append("file", file);
  return apiUpload<UploadResult>("/api/admin/documents/upload", formData);
}

export async function listDocuments(): Promise<IndexedDocument[]> {
  return apiGet<IndexedDocument[]>("/api/admin/documents");
}

export async function supersedeDocument(documentId: string): Promise<void> {
  await apiPost(`/api/admin/documents/${documentId}/supersede`);
}

export async function searchPreview(
  query: string,
  topK = 5
): Promise<SearchPreviewResult[]> {
  const params = new URLSearchParams({ q: query, top_k: String(topK) });
  return apiGet<SearchPreviewResult[]>(`/api/admin/search-preview?${params}`);
}
