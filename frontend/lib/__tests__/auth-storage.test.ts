import * as SecureStore from 'expo-secure-store';

import { clearTokens, getAccessToken, getRefreshToken, saveTokens } from '../auth-storage';

jest.mock('expo-secure-store', () => ({
  setItemAsync: jest.fn(),
  getItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

describe('auth-storage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('saveTokens stores the access and refresh tokens under their own keys', async () => {
    await saveTokens('access-123', 'refresh-456');

    expect(SecureStore.setItemAsync).toHaveBeenCalledWith('access_token', 'access-123');
    expect(SecureStore.setItemAsync).toHaveBeenCalledWith('refresh_token', 'refresh-456');
  });

  it('getAccessToken reads the access token key', async () => {
    (SecureStore.getItemAsync as jest.Mock).mockResolvedValueOnce('stored-access');

    await expect(getAccessToken()).resolves.toBe('stored-access');
    expect(SecureStore.getItemAsync).toHaveBeenCalledWith('access_token');
  });

  it('getRefreshToken reads the refresh token key', async () => {
    (SecureStore.getItemAsync as jest.Mock).mockResolvedValueOnce('stored-refresh');

    await expect(getRefreshToken()).resolves.toBe('stored-refresh');
    expect(SecureStore.getItemAsync).toHaveBeenCalledWith('refresh_token');
  });

  it('returns null when no token has been stored', async () => {
    (SecureStore.getItemAsync as jest.Mock).mockResolvedValueOnce(null);

    await expect(getAccessToken()).resolves.toBeNull();
  });

  it('clearTokens deletes both keys', async () => {
    await clearTokens();

    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('access_token');
    expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('refresh_token');
  });
});
