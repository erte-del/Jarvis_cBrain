// Main image + version strip + download. (Phase 4c)
// Click the image to select it, so "make this one black and white" knows which one you mean.

import { useState } from 'react'
import { API_BASE, type ImageCardData, type ImageSelection } from '../ws'

interface ImageViewerProps {
  data: ImageCardData
  selected: ImageSelection | null
  onSelect: (selection: ImageSelection | null) => void
}

export default function ImageViewer({ data, selected, onSelect }: ImageViewerProps) {
  // The version you clicked in the strip. It only counts until the image changes:
  // when a new version arrives (an edit or an undo), the viewer shows that one.
  const [pick, setPick] = useState<{ version: number; key: string } | null>(null)
  const key = `${data.current}/${data.versions.length}`
  const viewing = pick?.key === key ? pick.version : data.current

  const version = data.versions.find((v) => v.version === viewing) ?? data.versions[data.versions.length - 1]
  const isSelected = selected?.id === data.image_id

  const view = (n: number) => {
    setPick({ version: n, key })
    if (isSelected) onSelect({ id: data.image_id, version: n })
  }

  const toggleSelect = () =>
    onSelect(isSelected ? null : { id: data.image_id, version: version.version })

  const { credit } = data
  return (
    <div className="image-viewer">
      <button
        className={`image-main${isSelected ? ' selected' : ''}`}
        onClick={toggleSelect}
        title={isSelected ? 'Selected: click to unselect' : 'Click to select this image'}
      >
        <img src={API_BASE + version.url} alt={version.note} width={version.width} height={version.height} />
        {isSelected && <span className="image-selected-tag">Selected</span>}
      </button>

      <div className="image-bar">
        <div className="version-strip" role="list">
          {data.versions.map((v) => (
            <button
              key={v.version}
              role="listitem"
              className={`version-thumb${v.version === version.version ? ' viewing' : ''}`}
              onClick={() => view(v.version)}
              title={`v${v.version}: ${v.note}`}
            >
              <img src={API_BASE + v.thumb_url} alt="" />
              <span>v{v.version}</span>
            </button>
          ))}
        </div>
        <a className="image-download" href={`${API_BASE}${version.url}?download=1`} title="Download this version">
          ↓ Download
        </a>
      </div>

      <div className="image-meta">
        <span>
          v{version.version} · {version.note} · {version.width}×{version.height}
        </span>
        {credit.photographer && (
          <span>
            Photo by{' '}
            <a href={credit.photographer_url} target="_blank" rel="noreferrer noopener">
              {credit.photographer}
            </a>{' '}
            on{' '}
            <a href={credit.source_url} target="_blank" rel="noreferrer noopener">
              {credit.source || 'Pexels'}
            </a>
          </span>
        )}
      </div>
    </div>
  )
}
