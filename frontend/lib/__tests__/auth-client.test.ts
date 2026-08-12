import { ApiError } from '../api';

jest.mock('../auth-storage', () => ({
  getAccessToken: jest.fn(),
  getRefreshToken: jest.fn(),
  saveTokens: jest.fn(),
  clearTokens: jest.fn(),
}));

jest.mock('../api', () => {
  const actual = jest.requireActual('../api');
  return {
    ...actual,
    refreshTokens: jest.fn(),
  };
});

import { getAccessToken, getRefreshToken, saveTokens, clearTokens } from '../auth-storage';
import { refreshTokens } from '../api';
import { authenticatedFetch, onSessionExpired } from '../auth-client';

const mockGetAccessToken = getAccessToken as jest.Mock;
const mockGetRefreshToken = getRefreshToken as jest.Mock;
const mockSaveTokens = saveTokens as jest.Mock;
const mockClearTokens = clearTokens as jest.Mock;
const mockRefreshTokens = refreshTokens as jest.Mock;

describe('authenticatedFetch', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('runs the request with the current access token when it succeeds', async () => {
    mockGetAccessToken.mockResolvedValue('valid-token');
    const requestFn = jest.fn().mockResolvedValue('ok');

    const result = await authenticatedFetch(requestFn);

    expect(result).toBe('ok');
    expect(requestFn).toHaveBeenCalledTimes(1);
    expect(requestFn).toHaveBeenCalledWith('valid-token');
    expect(mockRefreshTokens).not.toHaveBeenCalled();
  });

  it('notifies listeners and throws when there is no stored access token', async () => {
    mockGetAccessToken.mockResolvedValue(null);
    const listener = jest.fn();
    const unsubscribe = onSessionExpired(listener);

    await expect(authenticatedFetch(jest.fn())).rejects.toMatchObject({ status: 401 });

    expect(listener).toHaveBeenCalledTimes(1);
    unsubscribe();
  });

  it('refreshes the token and retries once when the request fails with 401', async () => {
    mockGetAccessToken.mockResolvedValue('expired-token');
    mockGetRefreshToken.mockResolvedValue('valid-refresh-token');
    mockRefreshTokens.mockResolvedValue({
      access_token: 'new-token',
      refresh_token: 'new-refresh',
      token_type: 'bearer',
    });

    const requestFn = jest
      .fn()
      .mockRejectedValueOnce(new ApiError(401, 'expired'))
      .mockResolvedValueOnce('ok-after-refresh');

    const result = await authenticatedFetch(requestFn);

    expect(result).toBe('ok-after-refresh');
    expect(requestFn).toHaveBeenNthCalledWith(1, 'expired-token');
    expect(requestFn).toHaveBeenNthCalledWith(2, 'new-token');
    expect(mockSaveTokens).toHaveBeenCalledWith('new-token', 'new-refresh');
  });

  it('propagates non-401 errors without attempting a refresh', async () => {
    mockGetAccessToken.mockResolvedValue('valid-token');
    const serverError = new ApiError(500, 'boom');
    const requestFn = jest.fn().mockRejectedValue(serverError);

    await expect(authenticatedFetch(requestFn)).rejects.toBe(serverError);
    expect(mockRefreshTokens).not.toHaveBeenCalled();
    expect(requestFn).toHaveBeenCalledTimes(1);
  });

  it('clears the session and notifies listeners when there is no refresh token to use', async () => {
    mockGetAccessToken.mockResolvedValue('expired-token');
    mockGetRefreshToken.mockResolvedValue(null);
    const listener = jest.fn();
    const unsubscribe = onSessionExpired(listener);

    const original401 = new ApiError(401, 'expired');
    const requestFn = jest.fn().mockRejectedValue(original401);

    await expect(authenticatedFetch(requestFn)).rejects.toBe(original401);

    expect(mockRefreshTokens).not.toHaveBeenCalled();
    expect(listener).toHaveBeenCalledTimes(1);
    expect(requestFn).toHaveBeenCalledTimes(1);
    unsubscribe();
  });

  it('clears the session and notifies listeners when the refresh call itself fails', async () => {
    mockGetAccessToken.mockResolvedValue('expired-token');
    mockGetRefreshToken.mockResolvedValue('stale-refresh-token');
    mockRefreshTokens.mockRejectedValue(new ApiError(401, 'refresh token expired'));

    const listener = jest.fn();
    const unsubscribe = onSessionExpired(listener);

    const original401 = new ApiError(401, 'expired');
    const requestFn = jest.fn().mockRejectedValue(original401);

    await expect(authenticatedFetch(requestFn)).rejects.toBe(original401);

    expect(mockClearTokens).toHaveBeenCalledTimes(1);
    expect(listener).toHaveBeenCalledTimes(1);
    unsubscribe();
  });

  it('shares a single refresh call across concurrent 401s instead of racing multiple refreshes', async () => {
    mockGetAccessToken.mockResolvedValue('expired-token');
    mockGetRefreshToken.mockResolvedValue('valid-refresh-token');
    mockRefreshTokens.mockResolvedValue({
      access_token: 'new-token',
      refresh_token: 'new-refresh',
      token_type: 'bearer',
    });

    function makeRequestFn() {
      let calls = 0;
      return jest.fn(async (token: string) => {
        calls += 1;
        if (calls === 1) throw new ApiError(401, 'expired');
        return `ok-with-${token}`;
      });
    }

    const requestFnA = makeRequestFn();
    const requestFnB = makeRequestFn();

    const [resultA, resultB] = await Promise.all([
      authenticatedFetch(requestFnA),
      authenticatedFetch(requestFnB),
    ]);

    expect(resultA).toBe('ok-with-new-token');
    expect(resultB).toBe('ok-with-new-token');
    expect(mockRefreshTokens).toHaveBeenCalledTimes(1);
  });

  it('stops notifying a listener after it unsubscribes', async () => {
    mockGetAccessToken.mockResolvedValue(null);
    const listener = jest.fn();
    const unsubscribe = onSessionExpired(listener);
    unsubscribe();

    await expect(authenticatedFetch(jest.fn())).rejects.toMatchObject({ status: 401 });

    expect(listener).not.toHaveBeenCalled();
  });
});
