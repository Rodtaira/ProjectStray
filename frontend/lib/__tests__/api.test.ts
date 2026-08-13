import {
  ApiError,
  createAnimal,
  createSighting,
  deleteAnimal,
  getMe,
  listAnimals,
  listSightings,
  login,
  refreshTokens,
  updateAnimal,
  updateSighting,
} from '../api';

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

  const sighting = {
    id: 's1',
    reporter_id: 'u1',
    description: 'cachorro caramelo',
    status: 'open' as const,
    latitude: -15.7,
    longitude: -47.9,
    created_at: '2026-01-01T00:00:00Z',
  };

  describe('listSightings', () => {
    it('fetches sightings with the bearer token', async () => {
      mockFetchOnce(200, [sighting]);

      const result = await listSightings('token');

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.local/api/v1/sightings',
        expect.objectContaining({
          headers: expect.objectContaining({ Authorization: 'Bearer token' }),
        })
      );
      expect(result).toEqual([sighting]);
    });
  });

  describe('createSighting', () => {
    it('posts the sighting payload with the bearer token', async () => {
      mockFetchOnce(200, sighting);

      const result = await createSighting('token', {
        description: 'cachorro caramelo',
        latitude: -15.7,
        longitude: -47.9,
      });

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.local/api/v1/sightings',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({ Authorization: 'Bearer token' }),
          body: JSON.stringify({
            description: 'cachorro caramelo',
            latitude: -15.7,
            longitude: -47.9,
          }),
        })
      );
      expect(result).toEqual(sighting);
    });
  });

  describe('updateSighting', () => {
    it('patches the given sighting id with the bearer token', async () => {
      const updated = { ...sighting, status: 'resolved' as const };
      mockFetchOnce(200, updated);

      const result = await updateSighting('token', 's1', { status: 'resolved' });

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.local/api/v1/sightings/s1',
        expect.objectContaining({
          method: 'PATCH',
          headers: expect.objectContaining({ Authorization: 'Bearer token' }),
          body: JSON.stringify({ status: 'resolved' }),
        })
      );
      expect(result).toEqual(updated);
    });
  });

  const animal = {
    id: 'a1',
    registered_by: 'u1',
    species: 'dog' as const,
    sex: 'unknown' as const,
    name: null,
    description: null,
    is_sterilized: false,
    status: 'stray' as const,
    created_at: '2026-01-01T00:00:00Z',
  };

  describe('listAnimals', () => {
    it('fetches animals with the bearer token', async () => {
      mockFetchOnce(200, [animal]);

      const result = await listAnimals('token');

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.local/api/v1/animals',
        expect.objectContaining({
          headers: expect.objectContaining({ Authorization: 'Bearer token' }),
        })
      );
      expect(result).toEqual([animal]);
    });
  });

  describe('createAnimal', () => {
    it('posts the animal payload with the bearer token', async () => {
      mockFetchOnce(200, animal);

      const result = await createAnimal('token', { species: 'dog' });

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.local/api/v1/animals',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({ Authorization: 'Bearer token' }),
          body: JSON.stringify({ species: 'dog' }),
        })
      );
      expect(result).toEqual(animal);
    });
  });

  describe('updateAnimal', () => {
    it('patches the given animal id with the bearer token', async () => {
      const updated = { ...animal, status: 'adopted' as const };
      mockFetchOnce(200, updated);

      const result = await updateAnimal('token', 'a1', { status: 'adopted' });

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.local/api/v1/animals/a1',
        expect.objectContaining({
          method: 'PATCH',
          headers: expect.objectContaining({ Authorization: 'Bearer token' }),
          body: JSON.stringify({ status: 'adopted' }),
        })
      );
      expect(result).toEqual(updated);
    });
  });

  describe('deleteAnimal', () => {
    it('sends a DELETE request with the bearer token', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => {
          throw new Error('no body on 204');
        },
      });

      const result = await deleteAnimal('token', 'a1');

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.test.local/api/v1/animals/a1',
        expect.objectContaining({
          method: 'DELETE',
          headers: expect.objectContaining({ Authorization: 'Bearer token' }),
        })
      );
      expect(result).toBeUndefined();
    });
  });
});
