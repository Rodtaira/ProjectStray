import { getAccessToken, getRefreshToken, saveTokens, clearTokens } from './auth-storage';
import { ApiError, refreshTokens } from './api';

type Listener = () => void;
const sessionExpiredListeners: Listener[] = [];

export function onSessionExpired(listener: Listener): () => void {
  sessionExpiredListeners.push(listener);
  return () => {
    const index = sessionExpiredListeners.indexOf(listener);
    if (index !== -1) sessionExpiredListeners.splice(index, 1);
  };
}

function notifySessionExpired() {
  sessionExpiredListeners.forEach((listener) => listener());
}

// Evita disparar N refreshes em paralelo se várias chamadas tomarem 401 ao
// mesmo tempo — todas esperam a mesma promise em vez de brigar entre si
// (cada refresh gera um refresh_token novo, então refreshes concorrentes
// se invalidariam mutuamente).
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const currentRefreshToken = await getRefreshToken();
    if (!currentRefreshToken) return null;

    try {
      const tokens = await refreshTokens(currentRefreshToken);
      await saveTokens(tokens.access_token, tokens.refresh_token);
      return tokens.access_token;
    } catch {
      await clearTokens();
      return null;
    }
  })();

  const result = await refreshPromise;
  refreshPromise = null;
  return result;
}

/**
 * Executa uma chamada autenticada. Se vier 401, tenta renovar o access
 * token via refresh e repete a chamada UMA vez. Se o refresh também falhar
 * (refresh token expirado/inválido), limpa a sessão e avisa quem estiver
 * escutando onSessionExpired — normalmente isso significa voltar pro login.
 */
export async function authenticatedFetch<T>(
  requestFn: (accessToken: string) => Promise<T>
): Promise<T> {
  const accessToken = await getAccessToken();

  if (!accessToken) {
    notifySessionExpired();
    throw new ApiError(401, 'Sessão não encontrada');
  }

  try {
    return await requestFn(accessToken);
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      const newAccessToken = await refreshAccessToken();
      if (!newAccessToken) {
        notifySessionExpired();
        throw err;
      }
      return requestFn(newAccessToken);
    }
    throw err;
  }
}
