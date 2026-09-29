// A generated video: a progress bar while it renders, then the player and a download.

import { API_BASE, type VideoCardData } from '../ws'

export default function VideoCard({ data }: { data: VideoCardData }) {
  const pct = Math.round(data.progress * 100)
  return (
    <div className="image-viewer">
      {data.status === 'done' ? (
        <video
          className="video-main"
          src={API_BASE + data.url}
          width={data.width}
          height={data.height}
          controls
          autoPlay
          loop
          muted
          playsInline
        />
      ) : (
        <div className="video-pending" style={{ aspectRatio: `${data.width} / ${data.height}` }}>
          {data.status === 'failed' ? (
            <span className="video-error">{data.error || 'The video could not be made.'}</span>
          ) : (
            <>
              <span>{pct < 100 ? `Making the video… ${pct}%` : 'Finishing…'}</span>
              <progress value={data.progress} max={1} aria-label="Video progress" />
              <span className="video-hint">A 5-second clip takes about 13 minutes. You can keep chatting.</span>
            </>
          )}
        </div>
      )}
      <div className="image-bar">
        <span className="video-prompt" title={data.prompt}>
          {data.prompt}
        </span>
        {data.status === 'done' && (
          <a className="image-download" href={`${API_BASE}${data.url}?download=1`} download={data.download_name}>
            ↓ Download
          </a>
        )}
      </div>
      <div className="image-meta">
        <span>
          {data.seconds} s · {data.width}×{data.height} · Wan 2.1, made on this Mac
        </span>
      </div>
    </div>
  )
}
