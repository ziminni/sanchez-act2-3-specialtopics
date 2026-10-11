import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError } from '../api/client';
export function useQuery<T>(key: string, load: (signal: AbortSignal) => Promise<T>) {
  const loader = useRef(load);
  loader.current = load;
  const [data, setData] = useState<T>();
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [version, setVersion] = useState(0);
  const retry = useCallback(() => setVersion((v) => v + 1), []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setData(undefined);
    loader
      .current(controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setData(value);
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setError(
            error instanceof ApiError
              ? error
              : new ApiError(0, 'Unable to load this page. Please try again.')
          );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [key, version]);
  return { data, error, loading, retry };
}
