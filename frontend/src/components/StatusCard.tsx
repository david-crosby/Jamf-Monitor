import React from 'react';
import { HealthStatus } from '../types';
import { getStatusColor, getStatusBgColor } from '../utils/helpers';

interface StatusCardProps {
  status: HealthStatus;
  count: number;
  percentage: number;
  total: number;
  onClick?: () => void;
}

export const StatusCard: React.FC<StatusCardProps> = ({
  status,
  count,
  percentage,
  total,
  onClick
}) => {
  const statusLabels = {
    [HealthStatus.HEALTHY]: 'Healthy',
    [HealthStatus.CAUTION]: 'Caution',
    [HealthStatus.UNHEALTHY]: 'Unhealthy'
  };

  return (
    <div
      className="status-card"
      style={{
        backgroundColor: getStatusBgColor(status),
        borderLeft: `4px solid ${getStatusColor(status)}`,
        padding: '1.5rem',
        borderRadius: '0.5rem',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.2s, box-shadow 0.2s'
      }}
      onClick={onClick}
      onMouseEnter={(e) => {
        if (onClick) {
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
        }
      }}
      onMouseLeave={(e) => {
        if (onClick) {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = 'none';
        }
      }}
    >
      <div style={{ marginBottom: '0.5rem' }}>
        <h3 style={{ 
          margin: 0, 
          fontSize: '0.875rem',
          fontWeight: 500,
          color: '#6b7280',
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        }}>
          {statusLabels[status]}
        </h3>
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
        <span style={{ 
          fontSize: '2.5rem', 
          fontWeight: 700,
          color: getStatusColor(status)
        }}>
          {count}
        </span>
        <span style={{ 
          fontSize: '1rem',
          color: '#6b7280'
        }}>
          / {total}
        </span>
      </div>
      <div style={{ marginTop: '0.5rem' }}>
        <div style={{
          backgroundColor: '#e5e7eb',
          height: '0.5rem',
          borderRadius: '0.25rem',
          overflow: 'hidden'
        }}>
          <div
            style={{
              backgroundColor: getStatusColor(status),
              height: '100%',
              width: `${percentage}%`,
              transition: 'width 0.3s ease'
            }}
          />
        </div>
        <p style={{ 
          margin: '0.5rem 0 0 0',
          fontSize: '0.875rem',
          color: '#6b7280'
        }}>
          {percentage.toFixed(1)}%
        </p>
      </div>
    </div>
  );
};
