export enum HealthStatus {
  HEALTHY = 'healthy',
  CAUTION = 'caution',
  UNHEALTHY = 'unhealthy'
}

export interface DeviceBasicInfo {
  id: number;
  name: string;
  serial_number: string;
  model: string;
  os_version: string;
  last_contact_time: string | null;
  last_inventory_update: string | null;
}

export interface HealthCheckResult {
  check_in_ok: boolean;
  recon_ok: boolean;
  has_failed_policies: boolean;
  has_failed_mdm_commands: boolean;
  has_pending_mdm_commands: boolean;
  is_compliant: boolean;
  smart_group_memberships: string[];
}

export interface DeviceHealth {
  device: DeviceBasicInfo;
  health: HealthCheckResult;
  status: HealthStatus;
  last_checked: string;
}

export interface DeviceListResponse {
  total: number;
  devices: DeviceHealth[];
  healthy_count: number;
  caution_count: number;
  unhealthy_count: number;
}

export interface StatusSummary {
  total: number;
  healthy: number;
  caution: number;
  unhealthy: number;
  percentages: {
    healthy: number;
    caution: number;
    unhealthy: number;
  };
}

export interface HealthThresholds {
  check_in_hours: number;
  recon_hours: number;
  pending_command_hours: number;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}
