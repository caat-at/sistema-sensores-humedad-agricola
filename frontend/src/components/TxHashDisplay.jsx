import { useState } from 'react'
import { Copy, ExternalLink, Check } from 'lucide-react'

function TxHashDisplay({ txHash, explorerUrl }) {
  const [copied, setCopied] = useState(false)

  const copyToClipboard = () => {
    navigator.clipboard.writeText(txHash)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const shortHash = `${txHash.substring(0, 10)}...${txHash.substring(txHash.length - 10)}`

  return (
    <div
      style={{
        background: 'var(--bg-light)',
        padding: '15px',
        borderRadius: '8px',
        marginTop: '15px',
        border: '1px solid var(--border-color)'
      }}
    >
      <div style={{ marginBottom: '10px' }}>
        <strong style={{ color: 'var(--primary-color)' }}>Transaction Hash:</strong>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        {/* TxHash Display */}
        <div
          style={{
            flex: 1,
            fontFamily: 'monospace',
            fontSize: '14px',
            background: 'white',
            padding: '10px',
            borderRadius: '6px',
            wordBreak: 'break-all',
            minWidth: '200px'
          }}
        >
          <span className="hidden-mobile">{txHash}</span>
          <span className="visible-mobile">{shortHash}</span>
        </div>

        {/* Copy Button */}
        <button
          onClick={copyToClipboard}
          className="btn btn-secondary btn-sm"
          style={{
            background: copied ? 'var(--success-color)' : '#6c757d',
            minWidth: '100px'
          }}
        >
          {copied ? (
            <>
              <Check size={16} />
              Copiado!
            </>
          ) : (
            <>
              <Copy size={16} />
              Copiar
            </>
          )}
        </button>

        {/* Explorer Link */}
        {explorerUrl && (
          <a
            href={explorerUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-sm"
            style={{
              background: 'var(--info-color)',
              color: 'white',
              textDecoration: 'none',
              minWidth: '100px'
            }}
          >
            <ExternalLink size={16} />
            Ver en Explorer
          </a>
        )}
      </div>
    </div>
  )
}

export default TxHashDisplay
