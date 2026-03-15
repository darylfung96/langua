import { Volume2 } from 'lucide-react';
import type { VocabWord } from '../types';
import { LANGUAGES } from '../types';

interface Props {
  vocabulary: VocabWord[];
  language: string;
  onJumpToVocab: (word: string) => void;
}

const VocabularyList = ({ vocabulary, language, onJumpToVocab }: Props) => {
  return (
    <div className="vocab-table-container glass-panel">
      <div className="card-header border-bottom">
        <h3>Vocabulary Breakdown</h3>
      </div>
      <div className="table-responsive">
        <table className="vocab-table">
          <thead>
            <tr>
              <th>Original Word</th>
              <th>Meaning in {LANGUAGES[language as keyof typeof LANGUAGES] || language}</th>
              <th>Equivalent Word in English</th>
            </tr>
          </thead>
          <tbody>
            {vocabulary.map((vocab, i) => (
              <tr key={i}>
                <td className="vocab-word">
                  <Volume2
                    size={16}
                    className="word-audio"
                    onClick={() => onJumpToVocab(vocab.word)}
                  />
                  {vocab.word}
                </td>
                <td>{vocab.meaning_in_target}</td>
                <td className="vocab-mnemonic">{vocab.equivalent_in_english}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default VocabularyList;
