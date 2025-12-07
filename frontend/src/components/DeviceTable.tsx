import React from 'react';
import { DeviceHealth, HealthStatus } from '../types';
import { formatDateTime, getStatusColor, getStatusLabel } from '../utils/helpers';

interface DeviceTableProps {
  devices: DeviceHealth[];
  onDeviceClick?: (device: DeviceHealth) => void;
}

export const DeviceTable: React.FC<DeviceTableProps> = ({ devices, onDeviceClick }) => {
  const getHealthIssues = (device: DeviceHealth): string[] => {
    const issues: string[] = [];
    
    if (!device.health.check_in_ok) {
      issues.push('Check-in overdue');
    }
    if (!device.health.recon_ok) {
      issues.push('Recon overdue');
    }
    if (device.health.has_failed_policies) {
      issues.push('Failed policies');
    }
    if (device.health.has_failed_mdm_commands) {
      issues.push('Failed MDM commands');
    }
    if (device.health.has_pending_mdm_commands) {
      issues.push('Pending MDM commands');
    }
    if (!device.health.is_compliant) {
      issues.push('Non-compliant');
    }
    if (device.health.smart_group_memberships.length > 0) {
      issues.push(`Groups: ${device.health.smart_group_memberships.join(', ')}`);
    }
    
    return issues;
  };

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ 
        width: '100%', 
        borderCollapse: 'collapse',
        backgroundColor: 'white',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        borderRadius: '0.5rem'
      }}>
        <thead>
          <tr style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
            <th style={headerStyle}>Status</th>
            <th style={headerStyle}>Name</th>
            <th style={headerStyle}>Model</th>
            <th style={headerStyle}>OS Version</th>
            <th style={headerStyle}>Serial Number</th>
            <th style={headerStyle}>Last Contact</th>
            <th style={headerStyle}>Last Recon</th>
            <th style={headerStyle}>Issues</th>
          </tr>
        </thead>
        <tbody>
          {devices.length === 0 ? (
            <tr>
              <td colSpan={8} style={{ 
                padding: '2rem',
                textAlign: 'center',
                color: '#6b7280'
              }}>
                No devices found
              </td>
            </tr>
          ) : (
            devices.map((device) => {
              const issues = getHealthIssues(device);
              return (
                <tr
                  key={device.device.id}
                  onClick={() => onDeviceClick?.(device)}
                  style={{
                    borderBottom: '1px solid #e5e7eb',
                    cursor: onDeviceClick ? 'pointer' : 'default',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    if (onDeviceClick) {
                      e.currentTarget.style.backgroundColor = '#f9fafb';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (onDeviceClick) {
                      e.currentTarget.style.backgroundColor = 'white';
                    }
                  }}
                >
                  <td style={{ ...cellStyle, textAlign: 'center' }}>
                    <div
                      style={{
                        display: 'inline-block',
                        width: '0.75rem',
                        height: '0.75rem',
                        borderRadius: '50%',
                        backgroundColor: getStatusColor(device.status)
                      }}
                      title={getStatusLabel(device.status)}
                    />
                  </td>
                  <td style={{ ...cellStyle, fontWeight: 500 }}>{device.device.name}</td>
                  <td style={cellStyle}>{device.device.model}</td>
                  <td style={cellStyle}>{device.device.os_version}</td>
                  <td style={{ ...cellStyle, fontFamily: 'monospace', fontSize: '0.875rem' }}>
                    {device.device.serial_number}
                  </td>
                  <td style={cellStyle}>{formatDateTime(device.device.last_contact_time)}</td>
                  <td style={cellStyle}>{formatDateTime(device.device.last_inventory_update)}</td>
                  <td style={cellStyle}>
                    {issues.length > 0 ? (
                      <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                        {issues.map((issue, idx) => (
                          <div key={idx} style={{ marginBottom: '0.25rem' }}>
                            {issue}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span style={{ color: '#22c55e' }}>No issues</span>
                    )}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
};

const headerStyle: React.CSSProperties = {
  padding: '0.75rem 1rem',
  textAlign: 'left',
  fontSize: '0.75rem',
  fontWeight: 600,
  color: '#374151',
  textTransform: 'uppercase',
  letterSpacing: '0.05em'
};

const cellStyle: React.CSSProperties = {
  padding: '1rem',
  fontSize: '0.875rem',
  color: '#1f2937'
};
