import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { Animal, CampaignCreate, listAnimals } from './lib/api';
import { authenticatedFetch } from './lib/auth-client';

type Props = {
  visible: boolean;
  onCancel: () => void;
  onSubmit: (data: CampaignCreate) => Promise<void>;
};

export function CreateCampaignModal({ visible, onCancel, onSubmit }: Props) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [goalAmount, setGoalAmount] = useState('');
  const [animalId, setAnimalId] = useState<string | null>(null);
  const [animals, setAnimals] = useState<Animal[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (visible) {
      authenticatedFetch((token) => listAnimals(token))
        .then(setAnimals)
        .catch(() => setAnimals([]));
    }
  }, [visible]);

  async function handleSubmit() {
    setError(null);
    const parsedGoal = parseFloat(goalAmount.replace(',', '.'));
    if (!title.trim() || !parsedGoal || parsedGoal <= 0) {
      setError('Preencha um título e uma meta válida.');
      return;
    }
    setLoading(true);
    try {
      await onSubmit({
        title: title.trim(),
        description: description.trim() || null,
        goal_amount: parsedGoal,
        animal_id: animalId,
      });
      setTitle('');
      setDescription('');
      setGoalAmount('');
      setAnimalId(null);
    } catch {
      setError('Não foi possível salvar. Tente de novo.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <Text style={styles.title}>Nova campanha</Text>

          <TextInput style={styles.input} placeholder="Título" value={title} onChangeText={setTitle} />
          <TextInput
            style={styles.input}
            placeholder="Descrição (opcional)"
            value={description}
            onChangeText={setDescription}
            multiline
          />
          <TextInput
            style={styles.input}
            placeholder="Meta em R$ (ex: 250.00)"
            value={goalAmount}
            onChangeText={setGoalAmount}
            keyboardType="decimal-pad"
          />

          {animals.length > 0 && (
            <>
              <Text style={styles.label}>Vincular a um animal (opcional)</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipRow}>
                <TouchableOpacity
                  style={[styles.chip, animalId === null && styles.chipActive]}
                  onPress={() => setAnimalId(null)}
                >
                  <Text style={[styles.chipText, animalId === null && styles.chipTextActive]}>
                    Nenhum
                  </Text>
                </TouchableOpacity>
                {animals.map((a) => (
                  <TouchableOpacity
                    key={a.id}
                    style={[styles.chip, animalId === a.id && styles.chipActive]}
                    onPress={() => setAnimalId(a.id)}
                  >
                    <Text style={[styles.chipText, animalId === a.id && styles.chipTextActive]}>
                      {a.name || a.species}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </>
          )}

          {error && <Text style={styles.error}>{error}</Text>}

          <View style={styles.actions}>
            <TouchableOpacity style={styles.cancelButton} onPress={onCancel} disabled={loading}>
              <Text style={styles.cancelText}>Cancelar</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.submitButton} onPress={handleSubmit} disabled={loading}>
              {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.submitText}>Salvar</Text>}
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'flex-end' },
  card: { backgroundColor: '#fff', borderTopLeftRadius: 16, borderTopRightRadius: 16, padding: 24, gap: 10 },
  title: { fontSize: 18, fontWeight: '700', marginBottom: 4 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 12 },
  label: { fontSize: 13, color: '#666', marginTop: 4 },
  chipRow: { flexDirection: 'row' },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#ccc',
    marginRight: 8,
  },
  chipActive: { backgroundColor: '#2563eb', borderColor: '#2563eb' },
  chipText: { color: '#333', fontWeight: '600', fontSize: 13 },
  chipTextActive: { color: '#fff' },
  error: { color: 'red' },
  actions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 12, marginTop: 8 },
  cancelButton: { padding: 12 },
  cancelText: { color: '#666', fontWeight: '600' },
  submitButton: { backgroundColor: '#2563eb', borderRadius: 8, paddingVertical: 12, paddingHorizontal: 20 },
  submitText: { color: '#fff', fontWeight: '600' },
});
