import { WebPage } from '@/components/web-pages/web-pages';
import { Job } from '@/components/api/jobs/api/jobs';

const API_URL = 'http://localhost:5000';

export const getDashboardAnalytics = async (): Promise<any> => {
  const response = await fetch(`${API_URL}/dashboard-analytics`);
  if (!response.ok) {
    throw new Error('Failed to fetch dashboard analytics');
  }
  return response.json();
};

export const getWebPages = async (
  limit: number,
  offset: number,
  sortBy: string,
  sortOrder: string,
  query: string
): Promise<{ total: number; data: WebPage[] }> => {
  const response = await fetch(
    `${API_URL}/web-pages?limit=${limit}&offset=${offset}&sort_by=${sortBy}&sort_order=${sortOrder}&query=${query}`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch web pages');
  }
  return response.json();
};

export const getJobs = async (
  limit: number = 10,
  offset: number = 0
): Promise<Job[]> => {
  const response = await fetch(
    `${API_URL}/api/jobs?limit=${limit}&offset=${offset}`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch jobs');
  }
  return response.json();
};

export const getJob = async (jobId: string): Promise<Job> => {
  const response = await fetch(`${API_URL}/api/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch job');
  }
  return response.json();
};

export const startCrawler = async (
  domain: string,
  depth: number,
  flags: any = {}
): Promise<any> => {
  const response = await fetch(`${API_URL}/start-crawler`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ domain, depth, flags }),
  });
  if (!response.ok) {
    throw new Error('Failed to start crawler');
  }
  return response.json();
};

export const stopCrawler = async (jobId: string): Promise<any> => {
  const response = await fetch(`${API_URL}/stop-crawler/${jobId}`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to stop crawler');
  }
  return response.json();
};

export const getCrawlerStatus = async (jobId: string): Promise<any> => {
  const response = await fetch(`${API_URL}/crawler-status/${jobId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch crawler status');
  }
  return response.json();
};

export const deleteJob = async (jobId: string): Promise<any> => {
  const response = await fetch(`${API_URL}/api/jobs/${jobId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete job');
  }
  return response.json();
};
