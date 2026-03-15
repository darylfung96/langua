import { Trash2 } from 'lucide-react';

interface SavedLyric {
  id: string;
  title: string;
  language: string;
  created_at: string;
}

interface Props {
  savedLyrics: SavedLyric[];
  pendingDeleteId: string | null;
  setPendingDeleteId: (id: string | null) => void;
  onLoad: (lyricId: string) => void;
  onDelete: (lyricId: string, e: React.MouseEvent) => void;
}

const SavedLyricsList = ({ savedLyrics, pendingDeleteId, setPendingDeleteId, onLoad, onDelete }: Props) => {
  if (savedLyrics.length === 0) return null;

  return (
    <div className="saved-lyrics-section glass-panel" style={{ marginTop: '2rem', padding: '1rem' }}>
      <h3 style={{ marginTop: 0, marginBottom: '1rem' }}>Saved Lyrics</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem' }}>
        {savedLyrics.map((lyric) => (
          <div
            key={lyric.id}
            onClick={() => onLoad(lyric.id)}
            style={{
              padding: '1rem',
              background: 'rgba(99, 102, 241, 0.1)',
              borderRadius: '0.5rem',
              cursor: 'pointer',
              transition: 'background 0.2s',
              border: '1px solid rgba(99, 102, 241, 0.3)'
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(99, 102, 241, 0.2)'}
            onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(99, 102, 241, 0.1)'}
          >
            <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--accent-primary)' }}>{lyric.title}</h4>
            <p style={{ margin: '0.5rem 0', fontSize: '0.875rem', opacity: 0.7 }}>Language: {lyric.language}</p>
            <p style={{ margin: '0.5rem 0', fontSize: '0.75rem', opacity: 0.5 }}>
              {new Date(lyric.created_at).toLocaleDateString()}
            </p>
            {pendingDeleteId === lyric.id ? (
              <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '0.75rem' }}>Delete this lyric?</span>
                <button
                  onClick={(e) => onDelete(lyric.id, e)}
                  style={{ background: '#ef4444', color: 'white', border: 'none', padding: '0.25rem 0.5rem', borderRadius: '0.25rem', cursor: 'pointer', fontSize: '0.75rem' }}
                >Yes, delete</button>
                <button
                  onClick={(e) => { e.stopPropagation(); setPendingDeleteId(null); }}
                  style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: 'none', padding: '0.25rem 0.5rem', borderRadius: '0.25rem', cursor: 'pointer', fontSize: '0.75rem' }}
                >Cancel</button>
              </div>
            ) : (
              <button
                onClick={(e) => onDelete(lyric.id, e)}
                style={{
                  marginTop: '0.5rem',
                  background: '#ef4444',
                  color: 'white',
                  border: 'none',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '0.25rem',
                  cursor: 'pointer',
                  fontSize: '0.75rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.25rem'
                }}
              >
                <Trash2 size={12} />
                Delete
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default SavedLyricsList;
