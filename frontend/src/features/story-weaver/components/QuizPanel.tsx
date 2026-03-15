import { Brain, Sparkles, RefreshCw, Loader2, CheckCircle2, XCircle, Trophy } from 'lucide-react';
import type { QuizData, QuizQuestion } from '../types';

interface Props {
  quizData: QuizData | null;
  isGeneratingQuiz: boolean;
  userAnswers: Record<number, string>;
  fillBlankInputs: Record<number, string>;
  quizSubmitted: boolean;
  quizScore: number;
  onGenerateQuiz: () => void;
  onAnswerSelect: (questionId: number, answer: string) => void;
  onFillBlankChange: (questionId: number, value: string) => void;
  onSubmitQuiz: () => void;
  onRetakeQuiz: () => void;
}

const isAnswerCorrect = (
  q: QuizQuestion,
  userAnswers: Record<number, string>,
  fillBlankInputs: Record<number, string>
): boolean => {
  if (q.type === 'fill_blank') {
    return (fillBlankInputs[q.id] || '').trim().toLowerCase() === q.correct_answer.toLowerCase();
  }
  return (userAnswers[q.id] || '').toLowerCase() === q.correct_answer.toLowerCase();
};

const QuizPanel = ({
  quizData, isGeneratingQuiz, userAnswers, fillBlankInputs, quizSubmitted, quizScore,
  onGenerateQuiz, onAnswerSelect, onFillBlankChange, onSubmitQuiz, onRetakeQuiz,
}: Props) => {
  return (
    <div className="quiz-container glass-panel">
      <div className="card-header border-bottom">
        <h3><Brain size={20} /> Vocabulary Quiz</h3>
        <button
          className="quiz-generate-btn"
          onClick={onGenerateQuiz}
          disabled={isGeneratingQuiz}
        >
          {isGeneratingQuiz ? (
            <><Loader2 size={16} className="spinner" /> Crafting Quiz...</>
          ) : quizData ? (
            <><RefreshCw size={16} /> New Quiz</>
          ) : (
            <><Sparkles size={16} /> Generate Quiz</>
          )}
        </button>
      </div>

      {!quizData && !isGeneratingQuiz && (
        <div className="quiz-empty-state">
          <Brain size={48} className="quiz-empty-icon" />
          <p>Test your memory! Generate a quiz based on the vocabulary words.</p>
          <button className="quiz-start-btn" onClick={onGenerateQuiz}>
            <Sparkles size={18} /> Generate Quiz
          </button>
        </div>
      )}

      {isGeneratingQuiz && (
        <div className="quiz-loading">
          <div className="quiz-loading-dots">
            <span></span><span></span><span></span>
          </div>
          <p>Crafting your personalized quiz...</p>
        </div>
      )}

      {quizData && !isGeneratingQuiz && (
        <div className="quiz-content">
          {quizSubmitted && (
            <div className={`quiz-score-banner ${quizScore === quizData.questions.length ? 'perfect' : quizScore >= quizData.questions.length * 0.7 ? 'great' : 'keep-trying'}`}>
              <Trophy size={28} />
              <div>
                <div className="quiz-score-number">{quizScore} / {quizData.questions.length}</div>
                <div className="quiz-score-message">
                  {quizScore === quizData.questions.length ? '🎉 Perfect! You nailed it!' :
                    quizScore >= quizData.questions.length * 0.7 ? '🌟 Great job! Keep it up!' :
                      '💪 Keep practicing — you\'ve got this!'}
                </div>
              </div>
              <button className="quiz-retake-btn" onClick={onRetakeQuiz}>
                <RefreshCw size={16} /> Retake
              </button>
            </div>
          )}

          <div className="quiz-questions">
            {quizData.questions.map((q, idx) => {
              const answered = q.type === 'fill_blank'
                ? !!fillBlankInputs[q.id]?.trim()
                : !!userAnswers[q.id];
              const correct = quizSubmitted ? isAnswerCorrect(q, userAnswers, fillBlankInputs) : null;

              return (
                <div
                  key={q.id}
                  className={`quiz-question ${quizSubmitted ? (correct ? 'correct' : 'incorrect') : answered ? 'answered' : ''}`}
                >
                  <div className="quiz-question-header">
                    <span className="quiz-q-number">Q{idx + 1}</span>
                    <span className={`quiz-type-badge quiz-type-${q.type}`}>
                      {q.type === 'multiple_choice' ? 'Multiple Choice' :
                        q.type === 'fill_blank' ? 'Fill in the Blank' : 'True / False'}
                    </span>
                    {quizSubmitted && (
                      correct
                        ? <CheckCircle2 size={20} className="quiz-result-icon correct-icon" />
                        : <XCircle size={20} className="quiz-result-icon incorrect-icon" />
                    )}
                  </div>

                  <p className="quiz-question-text">{q.question}</p>

                  {q.type === 'fill_blank' ? (
                    <div className="quiz-fill-blank">
                      <input
                        type="text"
                        placeholder="Type your answer..."
                        value={fillBlankInputs[q.id] || ''}
                        onChange={(e) => onFillBlankChange(q.id, e.target.value)}
                        disabled={quizSubmitted}
                        className={`quiz-fill-input ${quizSubmitted ? (correct ? 'input-correct' : 'input-incorrect') : ''}`}
                      />
                      {quizSubmitted && !correct && (
                        <div className="quiz-correct-answer">
                          ✓ Correct: <strong>{q.correct_answer}</strong>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="quiz-options">
                      {q.options?.map((option) => {
                        const isSelected = userAnswers[q.id] === option;
                        const isCorrectOption = option.toLowerCase() === q.correct_answer.toLowerCase();
                        let optionClass = 'quiz-option';
                        if (quizSubmitted) {
                          if (isCorrectOption) optionClass += ' option-correct';
                          else if (isSelected && !isCorrectOption) optionClass += ' option-wrong';
                        } else if (isSelected) {
                          optionClass += ' option-selected';
                        }

                        return (
                          <button
                            key={option}
                            className={optionClass}
                            onClick={() => onAnswerSelect(q.id, option)}
                            disabled={quizSubmitted}
                          >
                            <span className="quiz-option-dot"></span>
                            {option}
                            {quizSubmitted && isCorrectOption && <CheckCircle2 size={16} className="option-check" />}
                            {quizSubmitted && isSelected && !isCorrectOption && <XCircle size={16} className="option-x" />}
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {quizSubmitted && (
                    <div className={`quiz-explanation ${correct ? 'explanation-correct' : 'explanation-incorrect'}`}>
                      💡 {q.explanation}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {!quizSubmitted && (
            <button
              className="quiz-submit-btn"
              onClick={onSubmitQuiz}
              disabled={quizData.questions.filter(q => q.type === 'fill_blank' ? !fillBlankInputs[q.id]?.trim() : !userAnswers[q.id]).length > 0}
            >
              <CheckCircle2 size={18} /> Check Answers
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default QuizPanel;
