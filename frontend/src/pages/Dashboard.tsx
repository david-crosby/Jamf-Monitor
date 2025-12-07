import React, { useState, useEffect } from 'react';
import { StatusCard } from '../components/StatusCard';
import { DeviceTable } from '../components/DeviceTable';
import { apiService } from '../services/api';
import { DeviceHealth, HealthStatus, StatusSummary, HealthThresholds } from '../types';

interface DashboardProps {
  onLogout: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onLogout }) => {
  const [devices, setDevices] = useState<DeviceHealth[]>([]);
  const [summary, setSummary] = useState<StatusSummary | null>(null);
  const [thresholds, setThresholds] = useState<HealthThresholds | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState<HealthStatus | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const loadData = async (filter?: HealthStatus | null) => {
    try {
      setLoading(true);
      setError('');
      
      const [devicesData, summaryData, thresholdsData] = await Promise.all([
        apiService.getAllDevices(filter || undefined),
        apiService.getStatusSummary(),
        apiService.getThresholds()
      ]);

      setDevices(devicesData.devices);
      setSummary(summaryData);
      setThresholds(thresholdsData);
    } catch (err) {
      setError('Failed to load data. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(statusFilter);
  }, [statusFilter]);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      loadData(statusFilter);
    }, 60000);

    return () => clearInterval(interval);
  }, [autoRefresh, statusFilter]);

  const handleStatusCardClick = (status: HealthStatus) => {
    setStatusFilter(statusFilter === status ? null : status);
  };

  const handleRefresh = () => {
    loadData(statusFilter);
  };

  const handleUpdateThresholds = async (newThresholds: HealthThresholds) => {
    try {
      await apiService.updateThresholds(newThresholds);
      setThresholds(newThresholds);
      loadData(statusFilter);
      setShowSettings(false);
    } catch (err) {
      setError('Failed to update thresholds');
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f3f4f6' }}>
      <nav style={{
        backgroundColor: 'white',
        borderBottom: '1px solid #e5e7eb',
        padding: '1rem 2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700, color: '#1f2937' }}>
          Jamf Monitor
        </h1>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh
          </label>
          <button
            onClick={handleRefresh}
            style={buttonStyle}
          >
            Refresh
          </button>
          <button
            onClick={() => setShowSettings(!showSettings)}
            style={buttonStyle}
          >
            Settings
          </button>
          <button
            onClick={onLogout}
            style={{ ...buttonStyle, backgroundColor: '#dc2626' }}
          >
            Logout
          </button>
        </div>
      </nav>

      <main style={{ padding: '2rem' }}>
        {error && (
          <div style={{
            padding: '1rem',
            marginBottom: '1.5rem',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '0.5rem',
            color: '#991b1b'
          }}>
            {error}
          </div>
        )}

        {showSettings && thresholds && (
          <div style={{
            backgroundColor: 'white',
            padding: '1.5rem',
            borderRadius: '0.5rem',
            marginBottom: '1.5rem',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
          }}>
            <h2 style={{ marginTop: 0, fontSize: '1.25rem', fontWeight: 600 }}>
              Health Check Thresholds
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500 }}>
                  Check-in threshold (hours)
                </label>
                <input
                  type="number"
                  value={thresholds.check_in_hours}
                  onChange={(e) => setThresholds({ ...thresholds, check_in_hours: parseInt(e.target.value) })}
                  min="1"
                  max="168"
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500 }}>
                  Recon threshold (hours)
                </label>
                <input
                  type="number"
                  value={thresholds.recon_hours}
                  onChange={(e) => setThresholds({ ...thresholds, recon_hours: parseInt(e.target.value) })}
                  min="1"
                  max="168"
                  style={inputStyle}
                />
              </div>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500 }}>
                  Pending command threshold (hours)
                </label>
                <input
                  type="number"
                  value={thresholds.pending_command_hours}
                  onChange={(e) => setThresholds({ ...thresholds, pending_command_hours: parseInt(e.target.value) })}
                  min="1"
                  max="72"
                  style={inputStyle}
                />
              </div>
            </div>
            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={() => handleUpdateThresholds(thresholds)}
                style={buttonStyle}
              >
                Save Changes
              </button>
              <button
                onClick={() => {
                  setShowSettings(false);
                  loadData(statusFilter);
                }}
                style={{ ...buttonStyle, backgroundColor: '#6b7280' }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {summary && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '1.5rem',
            marginBottom: '2rem'
          }}>
            <StatusCard
              status={HealthStatus.HEALTHY}
              count={summary.healthy}
              percentage={summary.percentages.healthy}
              total={summary.total}
              onClick={() => handleStatusCardClick(HealthStatus.HEALTHY)}
            />
            <StatusCard
              status={HealthStatus.CAUTION}
              count={summary.caution}
              percentage={summary.percentages.caution}
              total={summary.total}
              onClick={() => handleStatusCardClick(HealthStatus.CAUTION)}
            />
            <StatusCard
              status={HealthStatus.UNHEALTHY}
              count={summary.unhealthy}
              percentage={summary.percentages.unhealthy}
              total={summary.total}
              onClick={() => handleStatusCardClick(HealthStatus.UNHEALTHY)}
            />
          </div>
        )}

        <div style={{
          backgroundColor: 'white',
          padding: '1.5rem',
          borderRadius: '0.5rem',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1rem'
          }}>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600 }}>
              Devices
              {statusFilter && (
                <span style={{ marginLeft: '0.5rem', fontSize: '1rem', fontWeight: 400, color: '#6b7280' }}>
                  (Filtered by {statusFilter})
                </span>
              )}
            </h2>
            {statusFilter && (
              <button
                onClick={() => setStatusFilter(null)}
                style={{ ...buttonStyle, fontSize: '0.875rem', padding: '0.5rem 1rem' }}
              >
                Clear filter
              </button>
            )}
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#6b7280' }}>
              Loading devices...
            </div>
          ) : (
            <DeviceTable devices={devices} />
          )}
        </div>
      </main>
    </div>
  );
};

const buttonStyle: React.CSSProperties = {
  padding: '0.5rem 1rem',
  backgroundColor: '#2563eb',
  color: 'white',
  border: 'none',
  borderRadius: '0.375rem',
  fontSize: '0.875rem',
  fontWeight: 500,
  cursor: 'pointer',
  transition: 'background-color 0.2s'
};

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '0.5rem',
  border: '1px solid #d1d5db',
  borderRadius: '0.375rem',
  fontSize: '1rem'
};
