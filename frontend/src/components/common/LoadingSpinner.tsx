

interface LoadingSpinnerProps {
  size?: number;
  color?: string;
}

/**
 * Reusable full-page loading spinner used as the Suspense fallback in App.tsx
 * and anywhere else a centred loading indicator is needed.
 */
export default function LoadingSpinner({ size = 32, color = 'var(--accent-primary, #6366f1)' }: LoadingSpinnerProps) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
      }}
    >
      <div
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          border: `3px solid ${color}`,
          borderTopColor: 'transparent',
          animation: 'spin 0.8s linear infinite',
        }}
      />
    </div>
  );
}
