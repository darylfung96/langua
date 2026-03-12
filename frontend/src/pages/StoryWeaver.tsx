import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Sparkles, Play, Pause, BookOpen, Volume2, Loader2 } from 'lucide-react';
import { GoogleGenAI } from '@google/genai';
import './StoryWeaver.css';

interface VocabWord {
  word: string;
  meaning_in_target: string;
  equivalent_in_english: string;
}

interface StoryResponse {
  title: string;
  story: string;
  vocabulary: VocabWord[];
}

const createWavUrl = (base64Data: string, sampleRate = 24000) => {
  const binaryString = atob(base64Data);
  const pcmData = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    pcmData[i] = binaryString.charCodeAt(i);
  }

  const numChannels = 1;
  const bitsPerSample = 16;
  const header = new ArrayBuffer(44);
  const view = new DataView(header);

  const writeString = (v: DataView, offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      v.setUint8(offset + i, str.charCodeAt(i));
    }
  };

  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + pcmData.length, true);
  writeString(view, 8, 'WAVE');

  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * numChannels * (bitsPerSample / 8), true);
  view.setUint16(32, numChannels * (bitsPerSample / 8), true);
  view.setUint16(34, bitsPerSample, true);

  writeString(view, 36, 'data');
  view.setUint32(40, pcmData.length, true);

  const wavArray = new Uint8Array(44 + pcmData.length);
  wavArray.set(new Uint8Array(header), 0);
  wavArray.set(pcmData, 44);

  const blob = new Blob([wavArray], { type: 'audio/wav' });
  return URL.createObjectURL(blob);
};

const StoryWeaver = () => {
  const apiKey = import.meta.env.VITE_GEMINI_API_KEY || '';
  const [language, setLanguage] = useState('French');
  const [inputWords, setInputWords] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [storyData, setStoryData] = useState<StoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Audio state
  const [isPlaying, setIsPlaying] = useState(false);
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    // Cleanup dynamic URL if needed (we'll use base64 mostly, but good practice)
    return () => {
      if (audioUrl && audioUrl.startsWith('blob:')) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  // Handle Playback State
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleEnded = () => setIsPlaying(false);
    const handlePause = () => setIsPlaying(false);
    const handlePlay = () => setIsPlaying(true);
    const handleTimeUpdate = () => setCurrentTime(audio.currentTime);
    const handleLoadedMetadata = () => setDuration(audio.duration);

    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('pause', handlePause);
    audio.addEventListener('play', handlePlay);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);

    return () => {
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('pause', handlePause);
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('timeupdate', handleTimeUpdate);
      audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
    };
  }, [audioUrl]);

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const storyWords = useMemo(() => {
    if (!storyData) return [];

    const result: { text: string; index: number; isHighlight: boolean; title?: string }[] = [];
    let currentIdx = 0;

    const parts = storyData.story.split(/(<span[^>]*>.*?<\/span>)/g);

    parts.forEach(part => {
      if (part.startsWith('<span')) {
        const titleMatch = part.match(/title='([^']+)'/);
        const contentMatch = part.match(/>([^<]+)<\//);
        const title = titleMatch ? titleMatch[1] : undefined;
        const content = contentMatch ? contentMatch[1] : '';

        const words = content.split(/\s+/).filter(Boolean);
        words.forEach(w => {
          currentIdx++;
          result.push({ text: w, index: currentIdx, isHighlight: true, title });
        });
      } else {
        const words = part.split(/\s+/).filter(Boolean);
        words.forEach(w => {
          currentIdx++;
          result.push({ text: w, index: currentIdx, isHighlight: false });
        });
      }
    });

    return result;
  }, [storyData]);

  const jumpToWord = (index: number, total: number) => {
    if (audioRef.current && duration) {
      const time = (index / total) * duration;
      audioRef.current.currentTime = time;
      if (!isPlaying) {
        audioRef.current.play().catch(e => console.error("Error playing audio on jump:", e));
      }
    }
  };

  const jumpToVocab = (word: string) => {
    const found = storyWords.find(w => w.text.toLowerCase().includes(word.toLowerCase()));
    if (found) {
      jumpToWord(found.index, storyWords.length);
    }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputWords.trim()) return;
    if (!apiKey.trim()) {
      setError('Please provide a Gemini API Key.');
      return;
    }

    setIsGenerating(true);
    setStoryData(null);
    setAudioUrl(null); // Reset audio for new story
    setIsPlaying(false);
    setError(null);

    try {
      const ai = new GoogleGenAI({ apiKey });
      const prompt = `Write a short, engaging story in ${language} that incorporates the following vocabulary words: ${inputWords}. 
      
      Return the result as a raw JSON object with this exact structure:
      {
        "title": "Story Title in ${language}",
        "story": "The story in ${language}, with the requested vocabulary words wrapped in <span class='highlight' title='English Translation'>word</span>. Make sure the HTML is exactly like this.",
        "vocabulary": [
          {
            "word": "The original word submitted by the user",
            "meaning_in_target": "The translated word in ${language}",
            "equivalent_in_english": "The equivalent word in English"
          }
        ]
      }
      
      Ensure your response is ONLY valid JSON, without any markdown formatting like \`\`\`json.`;

      const response = await ai.models.generateContent({
        model: 'gemini-3.1-flash-lite-preview',
        contents: prompt,
      });

      if (!response.text) {
        throw new Error("No response from AI.");
      }

      let jsonText = response.text.trim();
      if (jsonText.startsWith('```json')) {
        jsonText = jsonText.replace(/^```json/, '').replace(/```$/, '').trim();
      } else if (jsonText.startsWith('```')) {
        jsonText = jsonText.replace(/^```/, '').replace(/```$/, '').trim();
      }

      const parsedData = JSON.parse(jsonText);
      setStoryData(parsedData);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'An error occurred while generating the story.');
    } finally {
      setIsGenerating(false);
    }
  };

  const generateAudio = async () => {
    if (!storyData || !apiKey.trim() || isGeneratingAudio) return;

    setIsGeneratingAudio(true);
    setError(null);

    try {
      const ai = new GoogleGenAI({ apiKey });
      // Strip HTML tags from the story for reading
      const cleanStory = storyData.story.replace(/<[^>]+>/g, '');
      const prompt = `Please read the following story aloud in ${language}:\n\n${storyData.title}\n\n${cleanStory}`;

      const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash-preview-tts',
        contents: prompt,
        config: {
          responseModalities: ["AUDIO"],
          speechConfig: {
            voiceConfig: {
              prebuiltVoiceConfig: {
                voiceName: 'Leda'
              }
            }
          }
        }
      });

      // Find the Audio part
      const audioPart = response.candidates?.[0]?.content?.parts?.find(p => p.inlineData?.mimeType?.startsWith('audio/'));

      if (audioPart && audioPart.inlineData && audioPart.inlineData.mimeType && audioPart.inlineData.data) {
        let url = '';
        if (audioPart.inlineData.mimeType.includes('pcm')) {
          url = createWavUrl(audioPart.inlineData.data);
        } else {
          url = `data:${audioPart.inlineData.mimeType};base64,${audioPart.inlineData.data}`;
        }
        setAudioUrl(url);
        // Play immediately after generating
        if (audioRef.current) {
          // wait for state update to load source, then play
          setTimeout(() => {
            audioRef.current?.play().catch(e => console.error("Error playing audio:", e));
          }, 0);
        }
      } else {
        throw new Error("No audio returned from the model.");
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'An error occurred while generating audio.');
    } finally {
      setIsGeneratingAudio(false);
    }
  };

  const toggleAudio = () => {
    if (!audioUrl) {
      // First time clicking listen, generate the audio
      generateAudio();
    } else if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play().catch(e => console.error("Error playing audio:", e));
      }
    }
  };

  return (
    <div className="page-container animate-fade-in story-weaver-page">
      <header className="page-header text-center">
        <h2 className="title-gradient">Story Weaver</h2>
        <p className="subtitle">Enter a few words and we'll weave them into a memorable story.</p>
      </header>

      <div className="story-weaver-grid">
        <div className="input-section glass-panel">
          <form onSubmit={handleGenerate}>
            <div className="input-group">
              <label htmlFor="language">Target Language</label>
              <select
                id="language"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  borderRadius: '0.5rem',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid rgba(255,255,255,0.1)',
                  color: 'white',
                  fontFamily: 'inherit',
                  marginBottom: '1rem',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                <option value="Spanish" style={{ color: 'black' }}>Spanish</option>
                <option value="French" style={{ color: 'black' }}>French</option>
                <option value="German" style={{ color: 'black' }}>German</option>
                <option value="Italian" style={{ color: 'black' }}>Italian</option>
                <option value="Japanese" style={{ color: 'black' }}>Japanese</option>
                <option value="Korean" style={{ color: 'black' }}>Korean</option>
                <option value="Chinese" style={{ color: 'black' }}>Chinese</option>
                <option value="Russian" style={{ color: 'black' }}>Russian</option>
                <option value="Portuguese" style={{ color: 'black' }}>Portuguese</option>
              </select>
            </div>
            <div className="input-group">
              <label htmlFor="words">Vocabulary Words</label>
              <textarea
                id="words"
                placeholder="e.g. gato, leche, rápido..."
                value={inputWords}
                onChange={(e) => setInputWords(e.target.value)}
                rows={4}
              />
              <p className="input-hint">Separate words with commas for best results.</p>
            </div>

            {error && <div className="error-message" style={{ color: '#ff6b6b', marginBottom: '1rem', fontSize: '0.875rem', padding: '0.5rem', background: 'rgba(255,107,107,0.1)', borderRadius: '0.25rem' }}>{error}</div>}

            <button
              type="submit"
              className={`generate-btn ${isGenerating ? 'generating' : ''}`}
              disabled={isGenerating || !inputWords.trim() || !apiKey.trim()}
            >
              {isGenerating ? (
                <>
                  <div className="spinner"></div>
                  Weaving Magic...
                </>
              ) : (
                <>
                  <Sparkles size={20} />
                  Weave Story
                </>
              )}
            </button>
          </form>
        </div>

        {storyData && (
          <div className="result-section animate-fade-in">
            <div className="story-card glass-panel">
              <div className="card-header">
                <h3><BookOpen size={20} /> {storyData.title}</h3>

                <button className="audio-btn" onClick={toggleAudio} disabled={isGeneratingAudio}>
                  {isGeneratingAudio ? (
                    <Loader2 size={18} className="spinner" />
                  ) : isPlaying ? (
                    <Pause size={18} />
                  ) : (
                    <Play size={18} />
                  )}
                  <span>{isGeneratingAudio ? 'Generating...' : isPlaying ? 'Pause' : 'Listen'}</span>
                  {isPlaying && <div className="audio-waves">
                    <span></span><span></span><span></span>
                  </div>}
                </button>
              </div>

              {audioUrl && (
                <div className="audio-controls-container" style={{ padding: '0 1.5rem 1.5rem' }}>
                  <audio ref={audioRef} src={audioUrl} />
                  <div className="audio-seekbar-row" style={{ display: 'flex', alignItems: 'center', gap: '1rem', width: '100%' }}>
                    <span style={{ fontSize: '0.75rem', opacity: 0.6, minWidth: '35px' }}>{formatTime(currentTime)}</span>
                    <input
                      type="range"
                      min="0"
                      max={duration || 0}
                      step="0.1"
                      value={currentTime}
                      onChange={handleSeek}
                      style={{
                        flex: 1,
                        accentColor: '#6366f1',
                        cursor: 'pointer',
                        height: '4px',
                        borderRadius: '2px'
                      }}
                    />
                    <span style={{ fontSize: '0.75rem', opacity: 0.6, minWidth: '35px' }}>{formatTime(duration)}</span>
                  </div>
                </div>
              )}

              <div className="story-content">
                <p>
                  {storyWords.map((w, i) => (
                    <React.Fragment key={i}>
                      <span
                        onClick={() => jumpToWord(w.index, storyWords.length)}
                        className={`${w.isHighlight ? 'highlight' : ''} clickable-word`}
                        title={w.title}
                      >
                        {w.text}
                      </span>
                      {' '}
                    </React.Fragment>
                  ))}
                </p>
              </div>
            </div>

            <div className="vocab-table-container glass-panel">
              <div className="card-header border-bottom">
                <h3>Vocabulary Breakdown</h3>
              </div>
              <div className="table-responsive">
                <table className="vocab-table">
                  <thead>
                    <tr>
                      <th>Original Word</th>
                      <th>Meaning in {language}</th>
                      <th>Equivalent Word in English</th>
                    </tr>
                  </thead>
                  <tbody>
                    {storyData.vocabulary.map((vocab, i) => (
                      <tr key={i}>
                        <td className="vocab-word">
                          <Volume2
                            size={16}
                            className="word-audio"
                            onClick={() => jumpToVocab(vocab.word)}
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
          </div>
        )}
      </div>
    </div>
  );
};

export default StoryWeaver;
