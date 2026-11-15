import { useEffect, useState } from 'react';

/**
 * Minimal request hook with a module-level promise cache, so moving between dashboard
 * pages does not refetch the same scenario. No global state library is needed.
 */

export type RequestStatus = 'idle' | 'loading' | 'success' | 'error';

type Settled<T> = { status: 'success'; data: T } | { status: 'error'; error: Error };

const cache = new Map<string, Promise<unknown>>();

export function clearRequestCache(): void {
  cache.clear();
}

export function hasCachedRequest(key: string): boolean {
  return cache.has(key);
}

export interface RequestState<T> {
  status: RequestStatus;
  data: T | undefined;
  error: Error | undefined;
  /** True while showing the previous key's data because the new key is still loading. */
  stale: boolean;
  retry: () => void;
}

interface RequestOptions {
  /** Keep showing the last successful result while a new key loads (no skeleton flash). */
  keepPrevious?: boolean;
}

export function useRequest<T>(
  key: string | null,
  fetcher: () => Promise<T>,
  options: RequestOptions = {},
): RequestState<T> {
  const [attempt, setAttempt] = useState(0);
  const [settled, setSettled] = useState<{ id: string; result: Settled<T> } | null>(null);
  const id = key === null ? null : `${key}#${attempt}`;

  useEffect(() => {
    if (key === null) return;
    let cancelled = false;
    let promise = cache.get(key) as Promise<T> | undefined;
    if (!promise) {
      promise = fetcher();
      cache.set(key, promise);
      // A failed request must not stay cached, so a retry really retries.
      promise.catch(() => cache.delete(key));
    }
    promise.then(
      (data) =>
        !cancelled && setSettled({ id: `${key}#${attempt}`, result: { status: 'success', data } }),
      (error: unknown) =>
        !cancelled &&
        setSettled({
          id: `${key}#${attempt}`,
          result: {
            status: 'error',
            error: error instanceof Error ? error : new Error(String(error)),
          },
        }),
    );
    return () => {
      cancelled = true;
    };
    // The key identifies the request; the fetcher's identity changes every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, attempt]);

  const current = settled && settled.id === id ? settled.result : null;
  const previous =
    options.keepPrevious && !current && settled?.result.status === 'success'
      ? settled.result.data
      : undefined;
  return {
    status: key === null ? 'idle' : current ? current.status : 'loading',
    data: current?.status === 'success' ? current.data : previous,
    error: current?.status === 'error' ? current.error : undefined,
    stale: previous !== undefined,
    retry: () => {
      if (key !== null) cache.delete(key);
      setAttempt((n) => n + 1);
    },
  };
}
