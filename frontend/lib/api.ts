const API_URL = process.env.EXPO_PUBLIC_API_URL;

export type AuthTokens = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type UserMe = {
  id: string;
  email: string;
  phone: string | null;
  full_name: string | null;
  role: string;
  created_at: string;
};

export type SightingStatus = 'open' | 'resolved';

export type Sighting = {
  id: string;
  reporter_id: string;
  description: string | null;
  status: SightingStatus;
  latitude: number;
  longitude: number;
  created_at: string;
};

export type SightingCreate = {
  description?: string | null;
  latitude: number;
  longitude: number;
};

export type SightingUpdate = {
  description?: string;
  status?: SightingStatus;
};

export type AnimalSpecies = 'dog' | 'cat';
export type AnimalSex = 'male' | 'female' | 'unknown';
export type AnimalStatus = 'stray' | 'adopted' | 'in_shelter' | 'deceased';

export type Animal = {
  id: string;
  registered_by: string;
  species: AnimalSpecies;
  sex: AnimalSex;
  name: string | null;
  description: string | null;
  is_sterilized: boolean;
  status: AnimalStatus;
  created_at: string;
};

export type AnimalCreate = {
  species: AnimalSpecies;
  sex?: AnimalSex;
  name?: string | null;
  description?: string | null;
};

export type AnimalUpdate = {
  name?: string;
  description?: string;
  sex?: AnimalSex;
  is_sterilized?: boolean;
  status?: AnimalStatus;
};

export type CampaignStatus = 'active' | 'funded' | 'completed' | 'cancelled';

export type Campaign = {
  id: string;
  created_by: string;
  animal_id: string | null;
  title: string;
  description: string | null;
  goal_amount: string; // Decimal vem como string do backend, preserva precisão
  status: CampaignStatus;
  created_at: string;
};

export type CampaignCreate = {
  title: string;
  description?: string | null;
  goal_amount: number;
  animal_id?: string | null;
};

export type CampaignUpdate = {
  title?: string;
  description?: string;
  status?: CampaignStatus;
};

export type DonationStatus = 'pending' | 'confirmed' | 'refunded';

export type Donation = {
  id: string;
  campaign_id: string;
  donor_id: string | null;
  amount: string;
  status: DonationStatus;
  created_at: string;
};

export type DonationCheckout = {
  donation: Donation;
  checkout_url: string;
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? `Erro ${res.status}`);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

export function login(email: string, password: string): Promise<AuthTokens> {
  return request('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export function refreshTokens(refreshToken: string): Promise<AuthTokens> {
  return request('/api/v1/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
}

export function getMe(accessToken: string): Promise<UserMe> {
  return request('/api/v1/users/me', {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export function listSightings(accessToken: string): Promise<Sighting[]> {
  return request('/api/v1/sightings', {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export function createSighting(accessToken: string, data: SightingCreate): Promise<Sighting> {
  return request('/api/v1/sightings', {
    method: 'POST',
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify(data),
  });
}

export function updateSighting(
  accessToken: string,
  id: string,
  data: SightingUpdate
): Promise<Sighting> {
  return request(`/api/v1/sightings/${id}`, {
    method: 'PATCH',
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify(data),
  });
}

export function listAnimals(accessToken: string): Promise<Animal[]> {
  return request('/api/v1/animals', {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

export function createAnimal(accessToken: string, data: AnimalCreate): Promise<Animal> {
  return request('/api/v1/animals', {
    method: 'POST',
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify(data),
  });
}

export function updateAnimal(
  accessToken: string,
  id: string,
  data: AnimalUpdate
): Promise<Animal> {
  return request(`/api/v1/animals/${id}`, {
    method: 'PATCH',
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify(data),
  });
}

export function deleteAnimal(accessToken: string, id: string): Promise<void> {
  return request(`/api/v1/animals/${id}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}

// Campanhas e doações são públicas na leitura — não exigem token.

export function listCampaigns(): Promise<Campaign[]> {
  return request('/api/v1/campaigns');
}

export function getCampaign(id: string): Promise<Campaign> {
  return request(`/api/v1/campaigns/${id}`);
}

export function createCampaign(accessToken: string, data: CampaignCreate): Promise<Campaign> {
  return request('/api/v1/campaigns', {
    method: 'POST',
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify(data),
  });
}

export function listCampaignDonations(campaignId: string): Promise<Donation[]> {
  return request(`/api/v1/campaigns/${campaignId}/donations`);
}

export function createDonation(
  accessToken: string,
  campaignId: string,
  amount: number
): Promise<DonationCheckout> {
  return request(`/api/v1/campaigns/${campaignId}/donations`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${accessToken}` },
    body: JSON.stringify({ amount }),
  });
}
