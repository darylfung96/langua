interface PhraseWord {
  text: string;
  difficulty?: 'easy' | 'medium' | 'hard';
}

interface Phrase {
  text: string;
  translation: string;
  words: PhraseWord[];
}

interface WordMatch {
  index: number;
  status: 'pending' | 'current' | 'matched' | 'missed';
  confidence?: number;
}

interface Props {
  phrases: Phrase[];
  currentPhraseIndex: number;
  wordMatches: WordMatch[];
}

const PhraseDisplay = ({ phrases, currentPhraseIndex, wordMatches }: Props) => {
  const currentPhrase = phrases[currentPhraseIndex];
  if (!currentPhrase) return null;

  return (
    <>
      <div className="phrase-words">
        {currentPhrase.words.map((word, idx) => (
          <span
            key={idx}
            className={`word ${wordMatches[idx]?.status || 'pending'}`}
          >
            {word.text}{' '}
          </span>
        ))}
      </div>

      <div className="translation">
        {currentPhrase.translation}
      </div>
    </>
  );
};

export default PhraseDisplay;
