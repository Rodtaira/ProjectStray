import * as React from 'react';
import { Text, TouchableOpacity, View } from 'react-native';
import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import { MapScreen } from '../MapScreen';
import { Sighting } from '../lib/api';

jest.mock('../lib/auth-client', () => ({
  authenticatedFetch: jest.fn((requestFn: (token: string) => unknown) => requestFn('token')),
}));

jest.mock('../lib/api', () => ({
  listSightings: jest.fn(),
  createSighting: jest.fn(),
  updateSighting: jest.fn(),
}));

jest.mock('expo-location', () => ({
  requestForegroundPermissionsAsync: jest.fn(),
  getCurrentPositionAsync: jest.fn(),
}));

jest.mock('react-native-maps', () => {
  const ReactMock = require('react');
  const RN = require('react-native');

  function MapView({ children, testID = 'map-view' }: any) {
    return ReactMock.createElement(RN.View, { testID }, children);
  }
  function Marker({ title, pinColor, onPress }: any) {
    return ReactMock.createElement(
      RN.TouchableOpacity,
      { testID: `marker-${title}-${pinColor}`, onPress },
      ReactMock.createElement(RN.Text, null, title)
    );
  }
  return { __esModule: true, default: MapView, Marker };
});

import { requestForegroundPermissionsAsync, getCurrentPositionAsync } from 'expo-location';
import { createSighting, listSightings, updateSighting } from '../lib/api';

const mockRequestPermission = requestForegroundPermissionsAsync as jest.Mock;
const mockGetPosition = getCurrentPositionAsync as jest.Mock;
const mockListSightings = listSightings as jest.Mock;
const mockCreateSighting = createSighting as jest.Mock;
const mockUpdateSighting = updateSighting as jest.Mock;

const openSighting: Sighting = {
  id: 's1',
  reporter_id: 'owner-1',
  description: 'cachorro caramelo',
  status: 'open',
  latitude: -15.7,
  longitude: -47.9,
  created_at: '2026-01-01T00:00:00Z',
};

function grantLocation() {
  mockRequestPermission.mockResolvedValue({ status: 'granted' });
  mockGetPosition.mockResolvedValue({ coords: { latitude: -15.7, longitude: -47.9 } });
}

describe('MapScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows an error message when location permission is denied', async () => {
    mockRequestPermission.mockResolvedValue({ status: 'denied' });
    mockListSightings.mockResolvedValue([]);

    render(<MapScreen currentUserId="owner-1" />);

    await waitFor(() =>
      expect(
        screen.getByText('Permissão de localização negada. Ative nas configurações do app.')
      ).toBeTruthy()
    );
  });

  it('renders a marker for each loaded sighting, colored by status', async () => {
    grantLocation();
    mockListSightings.mockResolvedValue([
      openSighting,
      { ...openSighting, id: 's2', status: 'resolved' },
    ]);

    render(<MapScreen currentUserId="owner-1" />);

    await waitFor(() =>
      expect(screen.getByTestId('marker-cachorro caramelo-red')).toBeTruthy()
    );
    expect(screen.getByTestId('marker-cachorro caramelo-green')).toBeTruthy();
  });

  it('stays usable when loading sightings fails (no markers, no crash)', async () => {
    grantLocation();
    mockListSightings.mockRejectedValue(new Error('network down'));

    render(<MapScreen currentUserId="owner-1" />);

    await waitFor(() => expect(screen.getByTestId('map-view')).toBeTruthy());
    expect(screen.queryByTestId(/^marker-/)).toBeNull();
  });

  it('opens the sighting detail modal when a marker is pressed', async () => {
    grantLocation();
    mockListSightings.mockResolvedValue([openSighting]);

    render(<MapScreen currentUserId="owner-1" />);

    await waitFor(() =>
      expect(screen.getByTestId('marker-cachorro caramelo-red')).toBeTruthy()
    );
    fireEvent.press(screen.getByTestId('marker-cachorro caramelo-red'));

    await waitFor(() => expect(screen.getByText('Marcar como resolvido')).toBeTruthy());
  });

  it('creates a sighting at the current position and adds a marker for it', async () => {
    grantLocation();
    mockListSightings.mockResolvedValue([]);
    mockCreateSighting.mockResolvedValue({ ...openSighting, id: 's3', description: 'gato preto' });

    render(<MapScreen currentUserId="owner-1" />);

    await waitFor(() => expect(screen.getByTestId('map-view')).toBeTruthy());
    fireEvent.press(screen.getByText('+'));
    fireEvent.changeText(
      screen.getByPlaceholderText('Ex: cachorro caramelo, parece perdido'),
      'gato preto'
    );
    fireEvent.press(screen.getByText('Salvar'));

    await waitFor(() =>
      expect(mockCreateSighting).toHaveBeenCalledWith('token', {
        description: 'gato preto',
        latitude: -15.7,
        longitude: -47.9,
      })
    );
    await waitFor(() =>
      expect(screen.getByTestId('marker-gato preto-red')).toBeTruthy()
    );
  });

  it('updates the marker color after resolving a sighting from the detail modal', async () => {
    grantLocation();
    mockListSightings.mockResolvedValue([openSighting]);
    mockUpdateSighting.mockResolvedValue({ ...openSighting, status: 'resolved' });

    render(<MapScreen currentUserId="owner-1" />);

    await waitFor(() =>
      expect(screen.getByTestId('marker-cachorro caramelo-red')).toBeTruthy()
    );
    fireEvent.press(screen.getByTestId('marker-cachorro caramelo-red'));
    await waitFor(() => expect(screen.getByText('Marcar como resolvido')).toBeTruthy());
    fireEvent.press(screen.getByText('Marcar como resolvido'));

    await waitFor(() =>
      expect(screen.getByTestId('marker-cachorro caramelo-green')).toBeTruthy()
    );
  });
});
