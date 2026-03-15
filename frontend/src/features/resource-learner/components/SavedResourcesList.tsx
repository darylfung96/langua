import React from 'react';
import { Trash2 } from 'lucide-react';

interface SavedResource {
  id: string;
  title: string;
  file_name: string;
  language: string;
  created_at: string;
}

interface Props {
  savedResources: SavedResource[];
  isLoadingSavedResources: boolean;
  pendingDeleteId: string | null;
  setPendingDeleteId?: (id: string | null) => void;
  onLoad: (resourceId: string) => void;
  onDelete: (resourceId: string, e: React.MouseEvent) => void;
}

const SavedResourcesList = ({
  savedResources,
  isLoadingSavedResources,
  pendingDeleteId,
  onLoad,
  onDelete,
}: Props) => {
  if (isLoadingSavedResources || savedResources.length === 0) return null;

  return (
    <div style={{ marginTop: '2rem', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '1.5rem' }}>
      <h3 style={{ marginBottom: '1rem', fontSize: '1rem', fontWeight: '600' }}>💾 Saved Resources</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', maxHeight: '300px', overflowY: 'auto' }}>
        {savedResources.map(resource => (
          <button
            key={resource.id}
            onClick={() => onLoad(resource.id)}
            style={{
              padding: '0.75rem',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '0.5rem',
              color: 'white',
              textAlign: 'left',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.1)';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.05)';
            }}
          >
            <div>
              <div style={{ fontSize: '0.9rem', fontWeight: '500' }}>{resource.title}</div>
              <div style={{ fontSize: '0.75rem', opacity: 0.6 }}>{resource.file_name}</div>
            </div>
            <button
              onClick={(e) => onDelete(resource.id, e)}
              style={{
                background: pendingDeleteId === resource.id ? 'rgba(255,107,107,0.5)' : 'rgba(255,107,107,0.2)',
                border: 'none',
                borderRadius: '0.25rem',
                padding: '0.25rem 0.5rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                color: '#ff6b6b',
                fontSize: pendingDeleteId === resource.id ? '0.7rem' : undefined,
              }}
              title={pendingDeleteId === resource.id ? 'Click again to confirm delete' : 'Delete'}
            >
              {pendingDeleteId === resource.id ? 'Confirm?' : <Trash2 size={14} />}
            </button>
          </button>
        ))}
      </div>
    </div>
  );
};

export default SavedResourcesList;
