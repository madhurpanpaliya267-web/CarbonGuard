import { useEffect, useState } from 'react'
import {
  Settings as SettingsIcon,
  AlertTriangle,
  Save,
  RotateCcw,
  Loader2,
  CheckCircle,
} from 'lucide-react'
import PageHeader from '@/shared/ui/PageHeader'
import { Card, CardTitle, CardContent } from '@/shared/ui/Card'
import Badge from '@/shared/ui/Badge'
import { api } from '@/shared/utils/api'
import type { SystemSetting } from '@/shared/types/common'

export default function SettingsPage() {
  const [settings, setSettings] = useState<SystemSetting[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState<string | null>(null)
  const [resetting, setResetting] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null)

  // Local edits
  const [edits, setEdits] = useState<Record<string, string>>({})

  useEffect(() => {
    async function load() {
      try {
        const s = await api.getSettings()
        setSettings(s)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  function handleEdit(key: string, value: string) {
    setEdits((prev) => ({ ...prev, [key]: value }))
  }

  async function handleSave(key: string) {
    const value = edits[key]
    if (value === undefined) return
    setSaving(key)
    setSaveSuccess(null)
    try {
      await api.updateSetting(key, value)
      setSettings((prev) =>
        prev.map((s) => (s.key === key ? { ...s, value } : s))
      )
      setSaveSuccess(key)
      setTimeout(() => setSaveSuccess(null), 2000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(null)
    }
  }

  async function handleReset() {
    setResetting(true)
    try {
      await api.resetSettings()
      const s = await api.getSettings()
      setSettings(s)
      setEdits({})
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset')
    } finally {
      setResetting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-10 h-10 border-2 border-border border-t-accent rounded-full animate-spin" />
      </div>
    )
  }

  // Group settings by category
  const grouped = settings.reduce<Record<string, SystemSetting[]>>((acc, s) => {
    const cat = s.category || 'general'
    if (!acc[cat]) acc[cat] = []
    acc[cat].push(s)
    return acc
  }, {})

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        subtitle="Configure Carbon Guard parameters and system preferences"
        badge={
          <Badge variant="muted" size="sm">
            <span className="inline-block w-1.5 h-1.5 bg-muted rounded-full animate-pulse mr-1" />
            CONFIGURATION
          </Badge>
        }
        actions={
          <button
            onClick={handleReset}
            disabled={resetting}
            className="flex items-center gap-2 px-3 py-1.5 bg-danger/10 text-danger text-xs font-medium rounded-md hover:bg-danger/20 transition-colors disabled:opacity-50"
          >
            {resetting ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <RotateCcw className="w-3 h-3" />
            )}
            Reset All
          </button>
        }
      />

      {/* Academic Notice */}
      <Card>
        <div className="flex items-center gap-3">
          <SettingsIcon className="w-4 h-4 text-muted" />
          <p className="text-xs text-muted">
            This is an academic simulation. Settings control estimation parameters
            for carbon calculations, optimization thresholds, and display preferences.
            No real infrastructure is controlled by these settings.
          </p>
        </div>
      </Card>

      {error && (
        <Card>
          <div className="flex items-center gap-3 text-danger">
            <AlertTriangle className="w-5 h-5" />
            <p className="text-sm">{error}</p>
          </div>
        </Card>
      )}

      {settings.length === 0 ? (
        <Card>
          <div className="text-center py-12">
            <SettingsIcon className="w-8 h-8 text-muted mx-auto mb-2" />
            <p className="text-sm text-muted">No settings found</p>
          </div>
        </Card>
      ) : (
        Object.entries(grouped).map(([category, items]) => (
          <Card key={category}>
            <div className="flex items-center gap-2 mb-4">
              <CardTitle className="capitalize">{category.replace('_', ' ')}</CardTitle>
              <Badge variant="muted" size="sm">{items.length} settings</Badge>
            </div>
            <CardContent>
              <div className="space-y-4">
                {items.map((setting) => {
                  const hasEdit = edits[setting.key] !== undefined
                  const currentValue = hasEdit ? edits[setting.key] : setting.value
                  const isSaving = saving === setting.key
                  const isSuccess = saveSuccess === setting.key
                  return (
                    <div key={setting.key} className="flex flex-col sm:flex-row sm:items-center gap-3 p-3 bg-background rounded-md">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-text-primary font-medium">{setting.key}</span>
                          {setting.description && (
                            <span className="text-[10px] text-muted">- {setting.description}</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={currentValue}
                          onChange={(e) => handleEdit(setting.key, e.target.value)}
                          className="px-3 py-1.5 bg-card border border-border rounded-md text-sm text-text-primary w-40 font-mono"
                        />
                        <button
                          onClick={() => handleSave(setting.key)}
                          disabled={isSaving || !hasEdit}
                          className={`p-1.5 rounded-md transition-colors ${
                            isSuccess
                              ? 'bg-success/20 text-success'
                              : hasEdit
                              ? 'bg-accent/10 text-accent hover:bg-accent/15'
                              : 'bg-card text-muted'
                          } disabled:opacity-50`}
                        >
                          {isSaving ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : isSuccess ? (
                            <CheckCircle className="w-4 h-4" />
                          ) : (
                            <Save className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  )
}
