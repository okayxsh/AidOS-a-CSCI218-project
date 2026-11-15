import { useEffect, useRef } from 'react';
import type { RequestStatus } from '../state/useRequest';

/**
 * When a user-started run finishes, move keyboard focus to its results. The button that
 * started the run disappears once results exist, so without this focus falls back to the
 * page body and keyboard and screen-reader users lose their place.
 */
export function useFocusAfterRun<T extends HTMLElement>(status: RequestStatus) {
  const ref = useRef<T>(null);
  const previous = useRef(status);
  useEffect(() => {
    if (previous.current === 'loading' && status === 'success') ref.current?.focus();
    previous.current = status;
  }, [status]);
  return ref;
}
