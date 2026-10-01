/**
 * Convert an array of objects to CSV string
 */
export function arrayToCSV<T extends Record<string, unknown>>(data: T[], headers?: string[]): string {
  if (data.length === 0) return ''
  const cols = headers || Object.keys(data[0])
  const rows = [cols.join(',')]
  for (const row of data) {
    rows.push(
      cols
        .map((col) => {
          const val = row[col]
          const str = val === null || val === undefined ? '' : String(val)
          return str.includes(',') || str.includes('"') || str.includes('\n')
            ? `"${str.replace(/"/g, '""')}"`
            : str
        })
        .join(','),
    )
  }
  return rows.join('\n')
}

/**
 * Trigger browser download of a string as a file
 */
export function downloadFile(content: string, filename: string, mimeType: string = 'text/csv'): void {
  const blob = new Blob([content], { type: `${mimeType};charset=utf-8;` })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Export security events to CSV
 */
export function exportEventsToCSV(
  events: Array<{
    id: number
    event_type: string
    severity: string
    timestamp: string
    source_ip: string
    target_ip: string
    target_port?: number | null
    confidence: number
    status: string
    estimated_energy_kwh?: number | null
    estimated_co2_kg?: number | null
    detection_method?: string | null
    description?: string | null
    risk_score?: number | null
  }>,
): void {
  const mapped = events.map((e) => ({
    ID: e.id,
    Type: e.event_type,
    Severity: e.severity,
    Timestamp: e.timestamp,
    'Source IP': e.source_ip,
    'Target IP': e.target_ip,
    'Target Port': e.target_port ?? '',
    Confidence: (e.confidence * 100).toFixed(0) + '%',
    Status: e.status,
    'Risk Score': e.risk_score?.toFixed(1) ?? '',
    'Energy (kWh)': e.estimated_energy_kwh?.toFixed(6) ?? '',
    'CO2 (kg)': e.estimated_co2_kg?.toFixed(6) ?? '',
    'Detection Method': e.detection_method ?? '',
    Description: e.description ?? '',
  }))
  const csv = arrayToCSV(mapped)
  downloadFile(csv, `carbonguard-events-${new Date().toISOString().slice(0, 10)}.csv`)
}

/**
 * Export threats to CSV
 */
export function exportThreatsToCSV(
  threats: Array<{
    id: number
    threat_type: string
    severity: string
    confidence: number
    risk_score: number
    status: string
    detected_at: string
    threat_uuid: string
    anomaly_level?: number | null
    recommended_action?: string | null
    explanation?: string | null
  }>,
): void {
  const mapped = threats.map((t) => ({
    ID: t.id,
    UUID: t.threat_uuid,
    Type: t.threat_type,
    Severity: t.severity,
    'Risk Score': t.risk_score.toFixed(1),
    Confidence: (t.confidence * 100).toFixed(0) + '%',
    'Anomaly Level': t.anomaly_level != null ? (t.anomaly_level * 100).toFixed(0) + '%' : '',
    Status: t.status,
    'Detected At': t.detected_at,
    'Recommended Action': t.recommended_action ?? '',
  }))
  const csv = arrayToCSV(mapped)
  downloadFile(csv, `carbonguard-threats-${new Date().toISOString().slice(0, 10)}.csv`)
}
