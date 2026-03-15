export interface GeneratedImage {
  id: number;
  type: string;
  url: string;
  base64: string;
}

export interface ImageResponse {
  word: string;
  language: string;
  prompt: string;
  images: GeneratedImage[];
  text_response: string;
  success: boolean;
}

export interface SavedVisual {
  id: string;
  word: string;
  language: string;
  created_at: string;
  updated_at: string;
}

export interface VisualDetail extends SavedVisual {
  images: GeneratedImage[];
  prompt: string;
  explanation: string;
}
