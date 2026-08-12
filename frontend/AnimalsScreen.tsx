import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { AnimalDetailModal } from './AnimalDetailModal';
import { CreateAnimalModal } from './CreateAnimalModal';
import {
  Animal,
  AnimalCreate,
  AnimalUpdate,
  createAnimal,
  deleteAnimal,
  listAnimals,
  updateAnimal,
} from './lib/api';
import { authenticatedFetch } from './lib/auth-client';

type Props = {
  currentUserId: string;
};

const SPECIES_LABELS: Record<string, string> = { dog: 'Cachorro', cat: 'Gato' };

export function AnimalsScreen({ currentUserId }: Props) {
  const [animals, setAnimals] = useState<Animal[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedAnimal, setSelectedAnimal] = useState<Animal | null>(null);

  const loadAnimals = useCallback(async () => {
    try {
      const data = await authenticatedFetch((token) => listAnimals(token));
      setAnimals(data);
    } catch {
      // lista fica vazia se falhar — tela continua utilizável
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAnimals();
  }, [loadAnimals]);

  async function handleCreateAnimal(data: AnimalCreate) {
    const newAnimal = await authenticatedFetch((token) => createAnimal(token, data));
    setAnimals((prev) => [newAnimal, ...prev]);
    setModalVisible(false);
  }

  async function handleUpdateAnimal(id: string, changes: AnimalUpdate) {
    const updated = await authenticatedFetch((token) => updateAnimal(token, id, changes));
    setAnimals((prev) => prev.map((a) => (a.id === id ? updated : a)));
    setSelectedAnimal(updated);
  }

  async function handleDeleteAnimal(id: string) {
    await authenticatedFetch((token) => deleteAnimal(token, id));
    setAnimals((prev) => prev.filter((a) => a.id !== id));
    setSelectedAnimal(null);
  }

  return (
    <View style={styles.container}>
      {loading ? (
        <ActivityIndicator style={styles.center} />
      ) : (
        <FlatList
          data={animals}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          ListEmptyComponent={<Text style={styles.empty}>Nenhum animal cadastrado ainda.</Text>}
          renderItem={({ item }) => (
            <TouchableOpacity style={styles.card} onPress={() => setSelectedAnimal(item)}>
              <View>
                <Text style={styles.cardTitle}>{item.name || SPECIES_LABELS[item.species]}</Text>
                <Text style={styles.cardSubtitle}>
                  {SPECIES_LABELS[item.species]} {item.is_sterilized ? '· Castrado' : ''}
                </Text>
              </View>
              <View
                style={[styles.badge, item.status === 'stray' ? styles.badgeStray : styles.badgeOther]}
              >
                <Text style={styles.badgeText}>{item.status}</Text>
              </View>
            </TouchableOpacity>
          )}
        />
      )}

      <TouchableOpacity style={styles.fab} onPress={() => setModalVisible(true)}>
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>

      <CreateAnimalModal
        visible={modalVisible}
        onCancel={() => setModalVisible(false)}
        onSubmit={handleCreateAnimal}
      />

      {selectedAnimal && (
        <AnimalDetailModal
          animal={selectedAnimal}
          currentUserId={currentUserId}
          onClose={() => setSelectedAnimal(null)}
          onUpdate={handleUpdateAnimal}
          onDelete={handleDeleteAnimal}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, justifyContent: 'center' },
  list: { padding: 16, gap: 10 },
  empty: { textAlign: 'center', color: '#666', marginTop: 40 },
  card: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 10,
    padding: 14,
  },
  cardTitle: { fontSize: 16, fontWeight: '600' },
  cardSubtitle: { color: '#666', marginTop: 2 },
  badge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 10 },
  badgeStray: { backgroundColor: '#fee2e2' },
  badgeOther: { backgroundColor: '#dcfce7' },
  badgeText: { fontSize: 11, fontWeight: '600' },
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
