import { ApiError, getMe, login, refreshTokens } from '../api';

function mockFetchOnce(status: number, body: unknown, ok = status >= 200 && status < 300) {
  (global.fetch as jest.Mock).mockResolvedValueOnce({
    ok,
    status,
    json: async () => body,
  });
}

describe('api', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  describe('login', () => {
    it('posts credentials to the login endpoint and returns tokens', async () => {
      const tokens = { access_token: 'a', refresh_token: 'r', token_type: 'bearer' };
      mockFetchOnce(200, tokens);

      const result = await login('user@example.com', 'hunter2');

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.local/api/v1/auth/login',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ email: 'user@example.com', password: 'hunter2' }),
          headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        })
      );
      expect(result).toEqual(tokens);
    });

    it('throws an ApiError carrying the status and server-provided detail', async () => {
      mockFetchOnce(401, { detail: 'Credenciais inválidas' });

      await expect(login('user@example.com', 'wrong')).rejects.toMatchObject({
        status: 401,
        message: 'Credenciais inválidas',
      });
    });

    it('falls back to a generic message when the error body is not JSON', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('not json');
        },
      });

      await expect(login('user@example.com', 'wrong')).rejects.toMatchObject({
        status: 500,
        message: 'Erro 500',
      });
    });

    it('rejects with an instance of ApiError', async () => {
      mockFetchOnce(429, { detail: 'Muitas tentativas' });

      await expect(login('a@b.com', 'x')).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe('refreshTokens', () => {
    it('posts the refresh token to the refresh endpoint', async () => {
      const tokens = { access_token: 'a2', refresh_token: 'r2', token_type: 'bearer' };
      mockFetchOnce(200, tokens);

      const result = await refreshTokens('old-refresh');

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.local/api/v1/auth/refresh',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ refresh_token: 'old-refresh' }),
        })
      );
      expect(result).toEqual(tokens);
    });
  });

  describe('getMe', () => {
    it('sends the access token as a bearer header', async () => {
      const user = {
        id: '1',
        email: 'user@example.com',
        phone: null,
        full_name: null,
        role: 'user',
        created_at: '2026-01-01T00:00:00Z',
      };
      mockFetchOnce(200, user);

      const result = await getMe('my-access-token');

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.local/api/v1/users/me',
        expect.objectContaining({
          headers: expect.objectContaining({ Authorization: 'Bearer my-access-token' }),
        })
      );
      expect(result).toEqual(user);
    });
  });
});
