/**
 * Utility to fetch YouTube subtitles.
 * Uses a public proxy to bypass CORS restrictions for development.
 * In a production environment, this should be handled by a proper backend.
 */

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
  /**
   * Fetches transcript for a given video ID
   */
  static async fetchTranscript(videoId: string, lang = 'en'): Promise<TranscriptData> {
    // Try local backend first
    try {
      const apiKey = import.meta.env.VITE_BACKEND_API_KEY;
      const baseUrl = `${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/youtube-transcript`;
      const videoUrl = `https://www.youtube.com/watch?v=${videoId}`;

      const response = await fetch(`${baseUrl}?url=${encodeURIComponent(videoUrl)}`, {
        headers: {
          'X-API-Key': apiKey || ''
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.segments && Array.isArray(data.segments)) {
          return {
            segments: data.segments.map((segment: any) => ({
              start: segment.start,
              duration: segment.end - segment.start,
              text: segment.text
            })),
            language: data.language || 'en'
          };
        }
      }
    } catch (error) {
      console.warn('Local backend failed, falling back to public APIs:', error);
    }

    // List of potential transcript API providers to try in sequence
    const apiProviders = [
      `https://youtube-transcript-api.vercel.app/api/transcript?videoId=${videoId}&lang=${lang}`,
      `https://yt-transcript-api.vercel.app/api/transcript?videoId=${videoId}&lang=${lang}` // Common alternative
    ];

    let lastError: any = null;

    for (const url of apiProviders) {
      try {
        const response = await fetch(url);

        if (!response.ok) {
          continue;
        }

        const data = await response.json();

        if (!data || (data.success === false && data.error)) {
          console.warn(`API ${url} returned an error:`, data.error);
          continue;
        }

        const transcriptArray = Array.isArray(data) ? data : (data.transcript || data.segments || data.result);

        if (!transcriptArray || !Array.isArray(transcriptArray)) {
          continue;
        }

        return {
          segments: transcriptArray.map((item: any) => ({
            start: parseFloat(item.offset ?? item.start ?? 0),
            duration: parseFloat(item.duration ?? 0),
            text: this.decodeHtmlEntities(item.text ?? '')
          })),
          language: lang
        };
      } catch (error: any) {
        lastError = error;
        console.warn(`Failed to fetch from ${url}:`, error.message);
      }
    }

    // If we reach here, all providers failed. 
    // Let's try one last "hack" - fetching from YouTube's internal timing API via CORS proxy
    try {
      return await this.fetchViaInternalApi(videoId, lang);
    } catch (finalError: any) {
      console.error('All transcript extraction methods failed:', finalError);
      throw new Error(lastError?.message || finalError.message || 'Could not fetch transcript. The video might not have captions enabled.');
    }
  }

  /**
   * Last resort: Try to fetch transcript via a CORS proxy to YouTube's internal player response
   */
  private static async fetchViaInternalApi(videoId: string, lang: string): Promise<TranscriptData> {
    const corsProxy = 'https://api.allorigins.win/get?url=';
    const ytUrl = encodeURIComponent(`https://www.youtube.com/watch?v=${videoId}`);

    const response = await fetch(`${corsProxy}${ytUrl}`);
    if (!response.ok) throw new Error('CORS proxy failed');

    const json = await response.json();
    const html = json.contents;

    // Look for player response in the HTML
    const match = html.match(/ytInitialPlayerResponse\s*=\s*({.+?});/);
    if (!match) throw new Error('Could not find player response in YouTube page');

    const playerResponse = JSON.parse(match[1]);
    const captionTracks = playerResponse.captions?.playerCaptionsTracklistRenderer?.captionTracks;

    if (!captionTracks || captionTracks.length === 0) {
      throw new Error('No captions found for this video.');
    }

    // Find preferred language or first available
    const track = captionTracks.find((t: any) => t.languageCode === lang) || captionTracks[0];
    const baseUrl = track.baseUrl;

    // Fetch the transcript content (it's XML)
    const transcriptResponse = await fetch(`${corsProxy}${encodeURIComponent(baseUrl)}`);
    if (!transcriptResponse.ok) throw new Error('Failed to fetch transcript XML');

    const transcriptJson = await transcriptResponse.json();
    const transcriptXml = transcriptJson.contents;

    // Parse the XML (browser built-in)
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(transcriptXml, "text/xml");
    const textNodes = xmlDoc.getElementsByTagName("text");

    const sections: TranscriptSection[] = [];
    for (let i = 0; i < textNodes.length; i++) {
      const node = textNodes[i];
      sections.push({
        start: parseFloat(node.getAttribute("start") || "0"),
        duration: parseFloat(node.getAttribute("dur") || "0"),
        text: this.decodeHtmlEntities(node.textContent || "")
      });
    }

    return {
      segments: sections,
      language: lang
    };
  }

  /**
   * Helper to decode HTML entities like &amp; or &#39;
   */
  private static decodeHtmlEntities(text: string): string {
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    return textarea.value;
  }

  /**
   * Extracts video ID from a YouTube URL
   */
  static extractVideoId(url: string): string | null {
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[7].length === 11) ? match[7] : null;
  }
}
