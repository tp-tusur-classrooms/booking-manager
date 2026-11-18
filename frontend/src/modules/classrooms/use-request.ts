import { useEffect, useState } from 'react';

type Result<T> =
  | { status: 'loading' }
  | { status: 'ready'; data: T }
  | { status: 'error'; error: unknown };

export function useRequest<T>(load: (signal: AbortSignal) => Promise<T>) {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<Result<T>>({ status: 'loading' });

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal).then(
      (data) => {
        if (!controller.signal.aborted) setResult({ status: 'ready', data });
      },
      (error: unknown) => {
        if (!controller.signal.aborted) setResult({ status: 'error', error });
      },
    );
    return () => controller.abort();
  }, [load, attempt]);

  return {
    result,
    retry: () => {
      setResult({ status: 'loading' });
      setAttempt((value) => value + 1);
    },
  };
}
