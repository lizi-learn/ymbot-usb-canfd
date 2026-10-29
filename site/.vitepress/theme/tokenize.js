// Shared build/browser tokenizer; compiled as normal JavaScript, never eval'd.
export function tokenize(text) {
  return Array.from(new Intl.Segmenter('zh-CN', { granularity: 'word' }).segment(text))
    .filter((part) => part.isWordLike).map((part) => part.segment.toLowerCase());
}
