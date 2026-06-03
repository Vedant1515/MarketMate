import React, { useEffect, useRef, useState, useCallback } from 'react'
import { fetchItems, logDailySales } from '../services/api'
import apiClient from '../services/api'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function today() {
  return new Date().toISOString().slice(0, 10)
}

// ---- Manual Entry Tab ----
function ManualTab({ onSaved }) {
  const [items, setItems] = useState([])
  const [date, setDate] = useState(today())
  const [quantities, setQuantities] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchItems()
      .then((data) => {
        setItems(data)
        const init = {}
        data.forEach((item) => { init[item.item] = '' })
        setQuantities(init)
        setLoading(false)
      })
      .catch(() => { setError('Failed to load items'); setLoading(false) })
  }, [])

  const handleSave = useCallback(async () => {
    const records = items
      .filter((item) => quantities[item.item] && parseFloat(quantities[item.item]) > 0)
      .map((item) => ({
        item: item.item,
        quantity_sold: parseFloat(quantities[item.item]),
        unit_price_aud: item.unit_price_aud,
        date,
      }))

    if (records.length === 0) { setError('Enter at least one quantity.'); return }

    setSaving(true); setError(null)
    try {
      const res = await logDailySales(records, date)
      setResult(res)
      onSaved && onSaved(res)
    } catch (err) {
      setError(err.message || 'Failed to save.')
    } finally {
      setSaving(false)
    }
  }, [items, quantities, date, onSaved])

  if (loading) return <div className="flex items-center justify-center h-32 text-text-secondary text-sm">Loading items...</div>

  if (result) return <SuccessPanel result={result} />

  return (
    <>
      <div className="px-5 py-3 border-b border-border flex-shrink-0">
        <label className="text-xs text-text-secondary font-mono block mb-1">Date</label>
        <input
          type="date" value={date} onChange={(e) => setDate(e.target.value)}
          className="bg-background border border-border rounded-lg px-3 py-1.5 text-sm text-text-primary font-mono focus:outline-none focus:border-accent/50"
        />
      </div>
      <div className="flex-1 overflow-y-auto">
        <table className="w-full font-mono text-xs">
          <thead className="sticky top-0 bg-surface border-b border-border">
            <tr>
              <th className="text-left px-5 py-2 text-text-secondary font-medium">Item</th>
              <th className="text-left px-3 py-2 text-text-secondary font-medium">Unit</th>
              <th className="text-right px-3 py-2 text-text-secondary font-medium">Price</th>
              <th className="text-right px-5 py-2 text-text-secondary font-medium">Qty sold</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.item} className="border-b border-border/50 hover:bg-background/40 transition-colors">
                <td className="px-5 py-2 text-text-primary font-medium">{item.item}</td>
                <td className="px-3 py-2 text-text-secondary">{item.unit}</td>
                <td className="px-3 py-2 text-right text-text-secondary">${item.unit_price_aud.toFixed(2)}</td>
                <td className="px-5 py-2">
                  <input
                    type="number" min="0" step="0.1" placeholder="0"
                    value={quantities[item.item] || ''}
                    onChange={(e) => setQuantities((p) => ({ ...p, [item.item]: e.target.value }))}
                    className="w-24 text-right bg-background border border-border rounded-lg px-2 py-1 text-text-primary focus:outline-none focus:border-accent/50 ml-auto block"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="px-5 py-4 border-t border-border flex items-center justify-between gap-3 flex-shrink-0">
        {error ? <p className="text-xs text-danger">{error}</p> : <p className="text-xs text-text-secondary">Leave blank to skip.</p>}
        <button
          onClick={handleSave} disabled={saving}
          className="px-4 py-2 rounded-lg bg-accent text-white text-xs font-semibold hover:bg-accent/90 disabled:opacity-50 transition-colors flex items-center gap-2 ml-auto"
        >
          {saving && <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
          {saving ? 'Saving...' : 'Save & Update AI'}
        </button>
      </div>
    </>
  )
}

// ---- Upload Tab ----
function UploadTab({ onSaved }) {
  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)

  const handleFile = useCallback((f) => {
    const allowed = ['csv', 'xlsx', 'xls']
    const ext = f.name.split('.').pop().toLowerCase()
    if (!allowed.includes(ext)) {
      setError(`Unsupported file type .${ext}. Use .xlsx, .xls, or .csv`)
      return
    }
    setFile(f)
    setError(null)
    setResult(null)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }, [handleFile])

  const handleUpload = useCallback(async () => {
    if (!file) return
    setUploading(true); setError(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await apiClient.post('/api/sales/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(res.data)
      onSaved && onSaved(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }, [file, onSaved])

  if (result) return <SuccessPanel result={result} isUpload />

  return (
    <>
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {/* Download template */}
        <div className="flex items-center justify-between p-3 rounded-lg border border-border bg-background">
          <div>
            <p className="text-xs font-semibold text-text-primary">Step 1 - Download the template</p>
            <p className="text-xs text-text-secondary mt-0.5">Pre-filled with your items. Fill in quantities per day.</p>
          </div>
          <div className="flex gap-2">
            <a
              href={`${BASE_URL}/api/sales/template?format=xlsx`}
              download="marketmate_sales_template.xlsx"
              className="px-3 py-1.5 rounded-lg border border-accent/30 bg-accent/10 text-xs text-accent font-mono hover:bg-accent/20 transition-colors"
            >
              Excel (.xlsx)
            </a>
            <a
              href={`${BASE_URL}/api/sales/template?format=csv`}
              download="marketmate_sales_template.csv"
              className="px-3 py-1.5 rounded-lg border border-border bg-surface text-xs text-text-secondary font-mono hover:text-text-primary transition-colors"
            >
              CSV
            </a>
          </div>
        </div>

        {/* Format info */}
        <div className="p-3 rounded-lg border border-border bg-background">
          <p className="text-xs font-semibold text-text-primary mb-2">Step 2 - Fill in your data</p>
          <p className="text-xs text-text-secondary mb-2">The template uses <strong className="text-text-primary">wide format</strong> - dates as rows, items as columns:</p>
          <pre className="text-xs font-mono bg-surface rounded p-2 text-text-secondary overflow-x-auto">
{`Date        Bananas  Avocados  Tomatoes  ...
2026-06-03  155.5    295       162       ...
2026-06-04  148.2    310       170       ...`}
          </pre>
          <p className="text-xs text-text-secondary mt-2">
            Also accepts <strong className="text-text-primary">long format</strong> with columns: date, item, quantity_sold, unit_price_aud
          </p>
        </div>

        {/* Drop zone */}
        <div>
          <p className="text-xs font-semibold text-text-primary mb-2">Step 3 - Upload your file</p>
          <div
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`
              border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
              ${dragging ? 'border-accent bg-accent/5' : 'border-border hover:border-accent/40 hover:bg-background/60'}
            `}
          >
            <input
              ref={inputRef} type="file" accept=".xlsx,.xls,.csv" className="hidden"
              onChange={(e) => { if (e.target.files[0]) handleFile(e.target.files[0]) }}
            />
            {file ? (
              <div className="space-y-1">
                <p className="text-sm font-semibold text-accent font-mono">{file.name}</p>
                <p className="text-xs text-text-secondary">{(file.size / 1024).toFixed(1)} KB - ready to upload</p>
                <button
                  onClick={(e) => { e.stopPropagation(); setFile(null) }}
                  className="text-xs text-text-secondary hover:text-danger transition-colors"
                >
                  Remove
                </button>
              </div>
            ) : (
              <div className="space-y-1">
                <p className="text-sm text-text-secondary">Drop your Excel or CSV file here</p>
                <p className="text-xs text-text-secondary/60">or click to browse - .xlsx, .xls, .csv</p>
              </div>
            )}
          </div>
        </div>

        {error && <p className="text-xs text-danger">{error}</p>}
      </div>

      <div className="px-5 py-4 border-t border-border flex-shrink-0 flex justify-end gap-2">
        <button
          onClick={handleUpload} disabled={!file || uploading}
          className="px-4 py-2 rounded-lg bg-accent text-white text-xs font-semibold hover:bg-accent/90 disabled:opacity-50 transition-colors flex items-center gap-2"
        >
          {uploading && <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
          {uploading ? 'Uploading...' : 'Upload & Update AI'}
        </button>
      </div>
    </>
  )
}

// ---- Shared Success Panel ----
function SuccessPanel({ result, isUpload }) {
  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-4">
      <div className="flex items-center gap-2">
        <span className="w-5 h-5 rounded-full bg-accent/20 border border-accent flex items-center justify-center text-accent text-xs font-bold">+</span>
        <span className="text-sm font-semibold text-text-primary">
          {isUpload ? 'File uploaded successfully' : 'Sales logged successfully'}
        </span>
      </div>

      <div className="font-mono text-xs space-y-1.5">
        {isUpload && result.dates_found?.length > 0 && (
          <div className="flex justify-between border-b border-border pb-1">
            <span className="text-text-secondary">Days imported</span>
            <span className="text-text-primary">{result.dates_found.join(', ')}</span>
          </div>
        )}
        {isUpload && result.items_found?.length > 0 && (
          <div className="flex justify-between border-b border-border pb-1">
            <span className="text-text-secondary">Items found</span>
            <span className="text-text-primary">{result.items_found.length} items</span>
          </div>
        )}
        <div className="flex justify-between border-b border-border pb-1">
          <span className="text-text-secondary">Records saved</span>
          <span className="text-accent">{result.rows_added}</span>
        </div>
        <div className="flex justify-between border-b border-border pb-1">
          <span className="text-text-secondary">ChromaDB updated</span>
          <span className="text-text-primary">{result.documents_reindexed} docs</span>
        </div>
        <div className="flex justify-between">
          <span className="text-text-secondary">Total weeks of data</span>
          <span className="text-text-primary">{result.total_weeks_of_data}</span>
        </div>
      </div>

      <p className="text-xs text-text-secondary italic">{result.message}</p>

      <div className="text-xs text-text-secondary bg-accent/5 border border-accent/20 rounded-lg p-3">
        RAG knowledge base updated. The AI will use this data immediately.
        {result.total_weeks_of_data >= 4 && (
          <span className="block mt-1 text-accent">
            You now have {result.total_weeks_of_data} weeks - demand forecasts are active.
          </span>
        )}
        {result.total_weeks_of_data < 4 && (
          <span className="block mt-1">
            Keep logging - forecasts improve after 4 weeks of data.
          </span>
        )}
      </div>
    </div>
  )
}

// ---- Main Modal ----
export default function SalesLogModal({ onClose, onSaved }) {
  const [tab, setTab] = useState('manual')

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-surface border border-border rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border flex-shrink-0">
          <div>
            <h2 className="text-sm font-semibold text-text-primary">Log Sales Data</h2>
            <p className="text-xs text-text-secondary mt-0.5">Every entry improves AI predictions over time.</p>
          </div>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary transition-colors text-xl leading-none px-1">x</button>
        </div>

        {/* Tab switcher */}
        <div className="flex border-b border-border flex-shrink-0">
          {[
            { key: 'manual', label: 'Manual Entry' },
            { key: 'upload', label: 'Upload Excel / CSV' },
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`px-5 py-2.5 text-xs font-mono transition-colors border-b-2 -mb-px ${
                tab === key
                  ? 'border-accent text-accent'
                  : 'border-transparent text-text-secondary hover:text-text-primary'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex flex-col flex-1 min-h-0">
          {tab === 'manual' ? (
            <ManualTab onSaved={onSaved} />
          ) : (
            <UploadTab onSaved={onSaved} />
          )}
        </div>

        {/* Footer cancel */}
        <div className="px-5 py-3 border-t border-border flex-shrink-0 flex justify-start">
          <button
            onClick={onClose}
            className="text-xs text-text-secondary hover:text-text-primary transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
