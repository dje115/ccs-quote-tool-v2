import { useEffect, useRef } from 'react';

/**
 * Hook that provides an AbortController that is automatically aborted
 * when the component unmounts, preventing state updates on unmounted components.
 * 
 * Usage:
 * ```tsx
 * const abortController = useAbortController();
 * 
 * useEffect(() => {
 *   const fetchData = async () => {
 *     try {
 *       const response = await apiClient.get('/endpoint', {
 *         signal: abortController.signal
 *       });
 *       // Handle response
 *     } catch (error) {
 *       if (error.name !== 'CanceledError') {
 *         // Handle error (ignore cancellation)
 *       }
 *     }
 *   };
 *   
 *   fetchData();
 * }, [abortController]);
 * ```
 */
export const useAbortController = () => {
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    // Create new AbortController on mount
    abortControllerRef.current = new AbortController();

    // Abort on unmount
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return abortControllerRef.current!;
};

/**
 * Hook that creates a new AbortController for each effect run
 * Useful when you want to cancel previous requests when dependencies change
 * 
 * Usage:
 * ```tsx
 * useEffect(() => {
 *   const abortController = new AbortController();
 *   
 *   const fetchData = async () => {
 *     try {
 *       const response = await apiClient.get('/endpoint', {
 *         signal: abortController.signal
 *       });
 *       // Handle response
 *     } catch (error) {
 *       if (error.name !== 'CanceledError') {
 *         // Handle error
 *       }
 *     }
 *   };
 *   
 *   fetchData();
 *   
 *   return () => {
 *     abortController.abort();
 *   };
 * }, [dependency]);
 * ```
 */
export const useAbortOnUnmount = () => {
  return useAbortController();
};

