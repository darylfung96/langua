interface Props {
  accuracy: number | null;
  interim: string;
  isListening: boolean;
  transcript: string;
  onClearRetry: () => void;
}

const AccuracyFeedback = ({ accuracy, interim, isListening, transcript, onClearRetry }: Props) => {
  return (
    <div className="feedback-panel">
      {accuracy !== null && (
        <div className="accuracy-display">
          <span className="accuracy-label">Accuracy</span>
          <span className={`accuracy-value ${accuracy >= 90 ? 'high' : accuracy >= 70 ? 'medium' : 'low'}`}>
            {accuracy}%
          </span>
        </div>
      )}
      {interim && (
        <div className="interim-text">
          <em>Hearing: {interim}</em>
        </div>
      )}
      {!isListening && transcript && (
        <button className="clear-transcript-btn" onClick={onClearRetry}>
          Clear & Retry
        </button>
      )}
    </div>
  );
};

export default AccuracyFeedback;
