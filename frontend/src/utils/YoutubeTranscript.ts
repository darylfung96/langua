import { apiFetch } from './apiClient';

export interface TranscriptSection {
  start: number;
  duration: number;
  text: string;
}

export interface TranscriptData {
  segments: TranscriptSection[];
  language: string;
}

export class YoutubeTranscript {
  static async fetchTranscript(videoId: string, lang = 'en'): Promise<TranscriptData> {
    const videoUrl = `https://www.youtube.com/watch?v=${videoId}`;
    const params = new URLSearchParams({ url: videoUrl, languages: lang });
    const response = await apiFetch(`/youtube-transcript?${params}`);
    const data = await response.json();

    if (!data.segments || !Array.isArray(data.segments)) {
      throw new Error('Could not fetch transcript. The video might not have captions enabled.');
    }

    return {
      segments: data.segments.map((segment: any) => ({
        start: segment.start,
        duration: segment.end - segment.start,
        text: segment.text,
      })),
      language: data.language || lang,
    };
  }

  static extractVideoId(url: string): string | null {
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[7].length === 11) ? match[7] : null;
  }
}
