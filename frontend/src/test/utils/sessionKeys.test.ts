import { describe, it, expect } from 'vitest';
import { SESSION_KEYS } from '../../utils/sessionKeys';

describe('SESSION_KEYS', () => {
  it('has all top-level feature namespaces', () => {
    expect(SESSION_KEYS).toHaveProperty('shadowing');
    expect(SESSION_KEYS).toHaveProperty('storyWeaver');
    expect(SESSION_KEYS).toHaveProperty('resourceLearner');
    expect(SESSION_KEYS).toHaveProperty('visualMemory');
  });

  it('all keys are non-empty strings', () => {
    function assertAllStrings(obj: unknown): void {
      if (typeof obj === 'string') {
        expect(obj.length).toBeGreaterThan(0);
      } else if (typeof obj === 'object' && obj !== null) {
        for (const v of Object.values(obj)) {
          assertAllStrings(v);
        }
      }
    }
    assertAllStrings(SESSION_KEYS);
  });

  it('has no duplicate key values across all namespaces', () => {
    const allValues: string[] = [];
    function collect(obj: unknown): void {
      if (typeof obj === 'string') {
        allValues.push(obj);
      } else if (typeof obj === 'object' && obj !== null) {
        for (const v of Object.values(obj)) collect(v);
      }
    }
    collect(SESSION_KEYS);
    const unique = new Set(allValues);
    expect(unique.size).toBe(allValues.length);
  });

  it('shadowing namespace has expected keys', () => {
    expect(SESSION_KEYS.shadowing).toMatchObject({
      theme: expect.any(String),
      language: expect.any(String),
      phrases: expect.any(String),
      currentIndex: expect.any(String),
    });
  });

  it('storyWeaver namespace has expected keys', () => {
    expect(SESSION_KEYS.storyWeaver).toMatchObject({
      language: expect.any(String),
      selectedStoryId: expect.any(String),
      storyData: expect.any(String),
    });
  });
});
