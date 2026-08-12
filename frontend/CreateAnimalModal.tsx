import { useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { AnimalCreate, AnimalSex, AnimalSpecies } from './lib/api';

type Props = {
  visible: boolean;
  onCancel: () => void;
  onSubmit: (data: AnimalCreate) => Promise<void>;
};

const SPECIES_OPTIONS: { value: AnimalSpecies; label: string }[] = [
  { value: 'dog', label: 'Cachorro' },
  { value: 'cat', label: 'Gato' },
];

const SEX_OPTIONS: { value: AnimalSex; label: string }[] = [
  { value: 'female', label: 'Fêmea' },
  { value: 'male', label: 'Macho' },
  { value: 'unknown', label: 'Não sei' },
];

export function CreateAnimalModal({ visible, onCancel, onSubmit }: Props) {
  const [species, setSpecies] = useState<AnimalSpecies>('dog');
  const [sex, setSex] = useState<AnimalSex>('unknown');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    setError(null);
    setLoading(true);
    try {
      await onSubmit({
        species,
        sex,
        name: name.trim() || null,
        description: description.trim() || null,
      });
      setName('');
      setDescription('');
      setSpecies('dog');
      setSex('unknown');
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
          <Text style={styles.title}>Cadastrar animal</Text>

          <Text style={styles.label}>Espécie</Text>
          <View style={styles.segmented}>
            {SPECIES_OPTIONS.map((opt) => (
              <TouchableOpacity
                key={opt.value}
                style={[styles.segment, species === opt.value && styles.segmentActive]}
                onPress={() => setSpecies(opt.value)}
              >
                <Text
                  style={[styles.segmentText, species === opt.value && styles.segmentTextActive]}
                >
                  {opt.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.label}>Sexo</Text>
          <View style={styles.segmented}>
            {SEX_OPTIONS.map((opt) => (
              <TouchableOpacity
                key={opt.value}
                style={[styles.segment, sex === opt.value && styles.segmentActive]}
                onPress={() => setSex(opt.value)}
              >
                <Text style={[styles.segmentText, sex === opt.value && styles.segmentTextActive]}>
                  {opt.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TextInput
            style={styles.input}
            placeholder="Nome (opcional)"
            value={name}
            onChangeText={setName}
          />
          <TextInput
            style={styles.input}
            placeholder="Descrição (cor, porte, características)"
            value={description}
            onChangeText={setDescription}
            multiline
          />

          {error && <Text style={styles.error}>{error}</Text>}

          <View style={styles.actions}>
            <TouchableOpacity style={styles.cancelButton} onPress={onCancel} disabled={loading}>
              <Text style={styles.cancelText}>Cancelar</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.submitButton} onPress={handleSubmit} disabled={loading}>
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.submitText}>Salvar</Text>
              )}
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
  label: { fontSize: 13, color: '#666', marginTop: 4 },
  segmented: { flexDirection: 'row', gap: 8 },
  segment: { flex: 1, paddingVertical: 10, borderRadius: 8, borderWidth: 1, borderColor: '#ccc', alignItems: 'center' },
  segmentActive: { backgroundColor: '#2563eb', borderColor: '#2563eb' },
  segmentText: { color: '#333', fontWeight: '600' },
  segmentTextActive: { color: '#fff' },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 12 },
  error: { color: 'red' },
  actions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 12, marginTop: 8 },
  cancelButton: { padding: 12 },
  cancelText: { color: '#666', fontWeight: '600' },
  submitButton: { backgroundColor: '#2563eb', borderRadius: 8, paddingVertical: 12, paddingHorizontal: 20 },
  submitText: { color: '#fff', fontWeight: '600' },
});
