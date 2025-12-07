import {
  DeviceListResponse,
  DeviceHealth,
  StatusSummary,
  HealthThresholds,
  LoginCredentials,
  AuthToken,
  HealthStatus
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiService {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` })
    };
  }

  async login(credentials: LoginCredentials): Promise<AuthToken> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    return data;
  }

  logout(): void {
    localStorage.removeItem('access_token');
  }

  isAuthenticated(): boolean {
    return localStorage.getItem('access_token') !== null;
  }

  async getAllDevices(statusFilter?: HealthStatus, useCache: boolean = true): Promise<DeviceListResponse> {
    const url = new URL(`${API_BASE_URL}/devices/`);
    if (statusFilter) {
      url.searchParams.append('status_filter', statusFilter);
    }
    url.searchParams.append('use_cache', useCache.toString());

    const response = await fetch(url.toString(), {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.logout();
        window.location.reload();
        throw new Error('Session expired');
      }
      throw new Error('Failed to fetch devices');
    }

    return response.json();
  }

  async getDeviceHealth(deviceId: number, useCache: boolean = true): Promise<DeviceHealth> {
    const url = new URL(`${API_BASE_URL}/devices/${deviceId}`);
    url.searchParams.append('use_cache', useCache.toString());

    const response = await fetch(url.toString(), {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.logout();
        window.location.reload();
        throw new Error('Session expired');
      }
      throw new Error('Failed to fetch device health');
    }

    return response.json();
  }

  async getStatusSummary(useCache: boolean = true): Promise<StatusSummary> {
    const url = new URL(`${API_BASE_URL}/devices/status/summary`);
    url.searchParams.append('use_cache', useCache.toString());

    const response = await fetch(url.toString(), {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.logout();
        window.location.reload();
        throw new Error('Session expired');
      }
      throw new Error('Failed to fetch status summary');
    }

    return response.json();
  }

  async getThresholds(): Promise<HealthThresholds> {
    const response = await fetch(`${API_BASE_URL}/settings/thresholds`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.logout();
        window.location.reload();
        throw new Error('Session expired');
      }
      throw new Error('Failed to fetch thresholds');
    }

    return response.json();
  }

  async updateThresholds(thresholds: HealthThresholds): Promise<HealthThresholds> {
    const response = await fetch(`${API_BASE_URL}/settings/thresholds`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(thresholds)
    });

    if (!response.ok) {
      if (response.status === 401) {
        this.logout();
        window.location.reload();
        throw new Error('Session expired');
      }
      throw new Error('Failed to update thresholds');
    }

    return response.json();
  }
}

export const apiService = new ApiService();
