/** Single source of truth for all supported language options across the app. */
export interface LanguageOption {
  value: string;
  label: string;
}

export const LANGUAGE_OPTIONS: readonly LanguageOption[] = [
  { value: 'en',    label: 'English' },
  { value: 'es',    label: 'Spanish' },
  { value: 'fr',    label: 'French' },
  { value: 'de',    label: 'German' },
  { value: 'it',    label: 'Italian' },
  { value: 'pt',    label: 'Portuguese' },
  { value: 'ja',    label: 'Japanese' },
  { value: 'zh-CN', label: 'Chinese (Simplified)' },
  { value: 'zh-TW', label: 'Chinese (Traditional)' },
  { value: 'ko',    label: 'Korean' },
  { value: 'ru',    label: 'Russian' },
  { value: 'ar',    label: 'Arabic' },
  { value: 'hi',    label: 'Hindi' },
  { value: 'nl',    label: 'Dutch' },
  { value: 'pl',    label: 'Polish' },
  { value: 'tr',    label: 'Turkish' },
] as const;
