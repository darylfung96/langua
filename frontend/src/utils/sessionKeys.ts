/** Centralised sessionStorage key constants — prevents typos and key collisions. */
export const SESSION_KEYS = {
  shadowing: {
    theme:        'sh_theme',
    language:     'sh_language',
    phrases:      'sh_phrases',
    currentIndex: 'sh_currentIndex',
  },
  storyWeaver: {
    language:        'sw_language',
    selectedStoryId: 'sw_selectedStoryId',
    storyData:       'sw_storyData',
    quizData:        'sw_quizData',
    quizScore:       'sw_quizScore',
    quizSubmitted:   'sw_quizSubmitted',
    userAnswers:     'sw_userAnswers',
    inputWords:      'sw_inputWords',
    fillBlankInputs: 'sw_fillBlankInputs',
  },
  resourceLearner: {
    status:             'rl_status',
    transcript:         'rl_transcript',
    language:           'rl_language',
    mediaFileType:      'rl_mediaFileType',
    selectedResourceId: 'rl_selectedResourceId',
  },
  visualMemory: {
    view:              'visualMemory_view',
    selectedVisualId:  'visualMemory_selectedVisualId',
  },
} as const;
