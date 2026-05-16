
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { callAPI } from './apiClient';

// Mock global fetch
const fetchSpy = vi.fn();

describe('apiClient Network Resilience', () => {
  beforeEach(() => {
    global.fetch = fetchSpy as any;
    fetchSpy.mockClear();
    fetchSpy.mockImplementation(() => 
      Promise.resolve(new Response(JSON.stringify({ success: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      }))
    );
  });

  it('should rewrite archon-server to localhost in browser environment', async () => {
    // 模擬瀏覽器環境
    vi.stubGlobal('window', {});
    
    // 模擬 VITE_API_URL 指向 Docker 內部 DNS
    vi.stubEnv('VITE_API_URL', 'http://archon-server:8181');

    await callAPI('/api/test');

    // 斷言：fetch 的第一個參數（Request 物件）的 URL 應該已經被重寫
    const lastCall = fetchSpy.mock.calls[0][0];
    const url = typeof lastCall === 'string' ? lastCall : lastCall.url;
    
    expect(url).toContain('http://localhost:8181/api/test');
  });

  it('should NOT rewrite if NOT in browser environment (e.g. Twin Scout Node context)', async () => {
    // 模擬非瀏覽器環境
    vi.stubGlobal('window', undefined);
    vi.stubEnv('VITE_API_URL', 'http://archon-server:8181');

    await callAPI('/api/test');

    // 斷言：保持原樣，這能讓 Docker 內部的 Scout 正常運作
    const lastCall = fetchSpy.mock.calls[0][0];
    const url = typeof lastCall === 'string' ? lastCall : lastCall.url;

    expect(url).toContain('http://archon-server:8181/api/test');
  });
});
