import { useEffect, useState } from 'react';

// Hook
export function useDebouncedValue(value, delay = 200) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

export function fuzzyIncludes(haystack, needle) {
  if (!needle) return true;
  haystack = (haystack || '').toLowerCase();
  needle = (needle || '').toLowerCase();

  let i = 0, j = 0, errors = 0;
  while (i < haystack.length && j < needle.length) {
    if (haystack[i] === needle[j]) j++;
    else if (haystack[i] === needle[j + 1]) { j += 2; errors++; }
    else if (haystack[i + 1] === needle[j]) { i++; errors++; }
    i++;
  }
  return j >= needle.length && errors <= Math.ceil(needle.length / 4);
}
