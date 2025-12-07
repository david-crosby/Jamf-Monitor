import { HealthStatus } from '../types';

export function formatDateTime(dateString: string | null): string {
  if (!dateString) return 'Never';
  
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const hours = Math.floor(diff / (1000 * 60 * 60));
  
  if (hours < 1) {
    const minutes = Math.floor(diff / (1000 * 60));
    return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
  }
  
  if (hours < 24) {
    return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
  }
  
  const days = Math.floor(hours / 24);
  if (days < 7) {
    return `${days} day${days !== 1 ? 's' : ''} ago`;
  }
  
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function getStatusColor(status: HealthStatus): string {
  switch (status) {
    case HealthStatus.HEALTHY:
      return '#22c55e';
    case HealthStatus.CAUTION:
      return '#eab308';
    case HealthStatus.UNHEALTHY:
      return '#ef4444';
    default:
      return '#6b7280';
  }
}

export function getStatusBgColor(status: HealthStatus): string {
  switch (status) {
    case HealthStatus.HEALTHY:
      return '#f0fdf4';
    case HealthStatus.CAUTION:
      return '#fefce8';
    case HealthStatus.UNHEALTHY:
      return '#fef2f2';
    default:
      return '#f9fafb';
  }
}

export function getStatusLabel(status: HealthStatus): string {
  switch (status) {
    case HealthStatus.HEALTHY:
      return 'Healthy';
    case HealthStatus.CAUTION:
      return 'Caution';
    case HealthStatus.UNHEALTHY:
      return 'Unhealthy';
    default:
      return 'Unknown';
  }
}

export function capitalise(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
