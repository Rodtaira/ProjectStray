import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import MapView, { Marker, Region } from 'react-native-maps';
import * as Location from 'expo-location';

import { CreateSightingModal } from './CreateSightingModal';
import { Sighting, createSighting, listSightings } from './lib/api';
import { authenticatedFetch } from './lib/auth-client';

export function MapScreen() {
  const [region, setRegion] = useState<Region | null>(null);
  const [sightings, setSightings] = useState<Sighting[]>([]);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [loadingSightings, setLoadingSightings] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);

  const loadSightings = useCallback(async () => {
    try {
      const data = await authenticatedFetch((token) => listSightings(token));
      setSightings(data);
    } catch {
      // Tela continua funcional mesmo se isso falhar — só sem os marcadores.
    } finally {
      setLoadingSightings(false);
    }
  }, []);

  useEffect(() => {
    (async () => {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setLocationError('Permissão de localização negada. Ative nas configurações do app.');
        return;
      }
      const position = await Location.getCurrentPositionAsync({});
      setRegion({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        latitudeDelta: 0.05,
        longitudeDelta: 0.05,
      });
    })();
  }, []);

  useEffect(() => {
    loadSightings();
  }, [loadSightings]);

  async function handleCreateSighting(description: string) {
    const position = await Location.getCurrentPositionAsync({});
    const newSighting = await authenticatedFetch((token) =>
      createSighting(token, {
        description: description || null,
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
      })
    );
    setSightings((prev) => [newSighting, ...prev]);
    setModalVisible(false);
  }

  if (locationError) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>{locationError}</Text>
      </View>
    );
  }

  if (!region) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <MapView style={styles.map} initialRegion={region} showsUserLocation>
        {sightings.map((sighting) => (
          <Marker
            key={sighting.id}
            coordinate={{ latitude: sighting.latitude, longitude: sighting.longitude }}
            title={sighting.description ?? 'Animal avistado'}
          />
        ))}
      </MapView>

      {loadingSightings && (
        <View style={styles.loadingBadge}>
          <ActivityIndicator size="small" />
        </View>
      )}

      <TouchableOpacity style={styles.fab} onPress={() => setModalVisible(true)}>
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>

      <CreateSightingModal
        visible={modalVisible}
        onCancel={() => setModalVisible(false)}
        onSubmit={handleCreateSighting}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  map: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  errorText: { textAlign: 'center', color: '#666' },
  loadingBadge: {
    position: 'absolute',
    top: 16,
    right: 16,
    backgroundColor: '#fff',
    padding: 8,
    borderRadius: 20,
    elevation: 3,
  },
  fab: {
    position: 'absolute',
    bottom: 24,
    right: 24,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#2563eb',
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 4,
  },
  fabText: { color: '#fff', fontSize: 28, fontWeight: '400', marginTop: -2 },
});
