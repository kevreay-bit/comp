import { useCallback, useEffect, useRef, useState } from 'react';

const API_URL = '/api/raffles';
const STREAM_URL = '/api/raffles/stream';

export function useRaffles(refreshInterval = 30000) {
  const [raffles, setRaffles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);

  const applyUpdates = useCallback((payload) => {
    if (!Array.isArray(payload)) return;
    setRaffles((prev) => {
      const map = new Map(prev.map((item) => [item.id, item]));
      payload.forEach((item) => {
        map.set(item.id, { ...map.get(item.id), ...item });
      });
      return Array.from(map.values());
    });
  }, []);

  const fetchRaffles = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(API_URL);
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }
      const data = await response.json();
      setRaffles(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRaffles();
    const intervalId = setInterval(fetchRaffles, refreshInterval);
    return () => clearInterval(intervalId);
  }, [fetchRaffles, refreshInterval]);

  useEffect(() => {
    const { protocol, host } = window.location;
    const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${host}${STREAM_URL}`;

    try {
      wsRef.current = new WebSocket(wsUrl);
      wsRef.current.addEventListener('message', (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload?.type === 'full-sync') {
            setRaffles(Array.isArray(payload.data) ? payload.data : []);
          } else if (payload?.type === 'patch') {
            applyUpdates(payload.data);
          } else {
            applyUpdates(payload);
          }
        } catch (err) {
          console.error('Failed to parse raffle update', err);
        }
      });
      wsRef.current.addEventListener('open', () => {
        setError(null);
      });
      wsRef.current.addEventListener('error', (event) => {
        console.warn('Raffle stream error', event);
      });
    } catch (err) {
      console.warn('WebSocket setup failed. Falling back to polling only.', err);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [applyUpdates]);

  return { raffles, loading, error, refetch: fetchRaffles };
}
