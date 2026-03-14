import { describe, it, expect } from 'vitest';
import { LANGUAGE_OPTIONS } from '../../utils/languages';

describe('LANGUAGE_OPTIONS', () => {
  it('is a non-empty array', () => {
    expect(Array.isArray(LANGUAGE_OPTIONS)).toBe(true);
    expect(LANGUAGE_OPTIONS.length).toBeGreaterThan(0);
  });

  it('every option has a non-empty value and label', () => {
    for (const option of LANGUAGE_OPTIONS) {
      expect(option.value).toBeTruthy();
      expect(option.label).toBeTruthy();
    }
  });

  it('contains common languages', () => {
    const values = LANGUAGE_OPTIONS.map((o) => o.value);
    expect(values).toContain('en');
    expect(values).toContain('es');
    expect(values).toContain('fr');
    expect(values).toContain('ja');
    expect(values).toContain('zh-CN');
  });

  it('has no duplicate values', () => {
    const values = LANGUAGE_OPTIONS.map((o) => o.value);
    const unique = new Set(values);
    expect(unique.size).toBe(values.length);
  });

  it('language codes match BCP 47 basic pattern', () => {
    const pattern = /^[a-zA-Z]{2,3}(?:-[a-zA-Z]{2,4})?$/;
    for (const option of LANGUAGE_OPTIONS) {
      expect(option.value).toMatch(pattern);
    }
  });
});
