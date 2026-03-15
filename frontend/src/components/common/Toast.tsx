

interface ToastProps {
  success?: string | null;
  error?: string | null;
}

/**
 * Inline toast messages for success and error feedback.
 * Renders nothing when both props are falsy.
 *
 * Usage:
 *   <Toast success={success} error={error} />
 */
export default function Toast({ success, error }: ToastProps) {
  if (!success && !error) return null;

  return (
    <>
      {error && (
        <div
          className="error-message"
          style={{
            color: '#ff6b6b',
            marginBottom: '1rem',
            fontSize: '0.875rem',
            padding: '0.5rem',
            background: 'rgba(255,107,107,0.1)',
            borderRadius: '0.25rem',
          }}
        >
          {error}
        </div>
      )}
      {success && (
        <div
          className="success-message"
          style={{
            color: '#51cf66',
            marginBottom: '1rem',
            fontSize: '0.875rem',
            padding: '0.5rem',
            background: 'rgba(81,207,102,0.1)',
            borderRadius: '0.25rem',
          }}
        >
          {success}
        </div>
      )}
    </>
  );
}
