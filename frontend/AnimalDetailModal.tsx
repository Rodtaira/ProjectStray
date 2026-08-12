import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { Animal, AnimalSex, AnimalStatus, AnimalUpdate } from './lib/api';

type Props = {
  animal: Animal;
  currentUserId: string;
  onClose: () => void;
  onUpdate: (id: string, changes: AnimalUpdate) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
};

const STATUS_LABELS: Record<AnimalStatus, string> = {
  stray: 'Na rua',
  adopted: 'Adotado',
  in_shelter: 'Em abrigo',
  deceased: 'Falecido',
};
const STATUS_OPTIONS: AnimalStatus[] = ['stray', 'adopted', 'in_shelter', 'deceased'];

const SEX_LABELS: Record<AnimalSex, string> = {
  male: 'Macho',
  female: 'Fêmea',
  unknown: 'Não sei',
};
const SEX_OPTIONS: AnimalSex[] = ['female', 'male', 'unknown'];

const SPECIES_LABELS: Record<string, string> = { dog: 'Cachorro', cat: 'Gato' };

export function AnimalDetailModal({ animal, currentUserId, onClose, onUpdate, onDelete }: Props) {
  const [editing, setEditing] = useState(false);
  const [description, setDescription] = useState(animal.description ?? '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isOwner = animal.registered_by === currentUserId;

  async function applyUpdate(changes: AnimalUpdate) {
    setLoading(true);
    setError(null);
    try {
      await onUpdate(animal.id, changes);
    } catch {
      setError('Não foi possível salvar a alteração.');
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveDescription() {
    await applyUpdate({ description: description.trim() });
    setEditing(false);
  }

  function handleDeletePress() {
    Alert.alert(
      'Remover cadastro',
      'Isso apaga o registro permanentemente e não pode ser desfeito. Se o animal foi adotado ou faleceu, use "Status" em vez disso — assim mantém o histórico. Remover é só pra corrigir um cadastro feito por engano.',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Remover mesmo assim',
          style: 'destructive',
          onPress: async () => {
            setLoading(true);
            setError(null);
            try {
              await onDelete(animal.id);
            } catch {
              setError('Não foi possível remover.');
              setLoading(false);
            }
          },
        },
      ]
    );
  }

  return (
    <Modal visible animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <View style={styles.header}>
            <Text style={styles.title}>{animal.name || SPECIES_LABELS[animal.species]}</Text>
            <TouchableOpacity onPress={onClose}>
              <Text style={styles.closeText}>Fechar</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.meta}>{SPECIES_LABELS[animal.species]}</Text>

          {editing ? (
            <TextInput
              style={styles.input}
              value={description}
              onChangeText={setDescription}
              multiline
              autoFocus
            />
          ) : (
            <Text style={styles.description}>{animal.description || 'Sem descrição'}</Text>
          )}

          <View style={styles.row}>
            <Text style={styles.label}>Castrado</Text>
            <Switch
              value={animal.is_sterilized}
              onValueChange={(value) => applyUpdate({ is_sterilized: value })}
              disabled={!isOwner || loading}
            />
          </View>

          <Text style={styles.label}>Sexo</Text>
          <View style={styles.segmented}>
            {SEX_OPTIONS.map((opt) => (
              <TouchableOpacity
                key={opt}
                style={[styles.segment, animal.sex === opt && styles.segmentActive]}
                onPress={() => applyUpdate({ sex: opt })}
                disabled={!isOwner || loading}
              >
                <Text style={[styles.segmentText, animal.sex === opt && styles.segmentTextActive]}>
                  {SEX_LABELS[opt]}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.label}>Status</Text>
          <View style={styles.segmented}>
            {STATUS_OPTIONS.map((opt) => (
              <TouchableOpacity
                key={opt}
                style={[styles.segment, animal.status === opt && styles.segmentActive]}
                onPress={() => applyUpdate({ status: opt })}
                disabled={!isOwner || loading}
              >
                <Text
                  style={[styles.segmentText, animal.status === opt && styles.segmentTextActive]}
                >
                  {STATUS_LABELS[opt]}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {error && <Text style={styles.error}>{error}</Text>}
          {loading && <ActivityIndicator />}

          {isOwner && (
            <View style={styles.actions}>
              {editing ? (
                <TouchableOpacity
                  style={styles.primaryButton}
                  onPress={handleSaveDescription}
                  disabled={loading}
                >
                  <Text style={styles.primaryText}>Salvar descrição</Text>
                </TouchableOpacity>
              ) : (
                <TouchableOpacity style={styles.secondaryButton} onPress={() => setEditing(true)}>
                  <Text style={styles.secondaryText}>Editar descrição</Text>
                </TouchableOpacity>
              )}

              <TouchableOpacity
                style={styles.deleteButton}
                onPress={handleDeletePress}
                disabled={loading}
              >
                <Text style={styles.deleteText}>Remover cadastro</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'flex-end' },
  card: { backgroundColor: '#fff', borderTopLeftRadius: 16, borderTopRightRadius: 16, padding: 24, gap: 12 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 18, fontWeight: '700' },
  closeText: { color: '#2563eb', fontWeight: '600' },
  meta: { color: '#666' },
  description: { fontSize: 16 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 12, minHeight: 60, textAlignVertical: 'top' },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  label: { fontSize: 13, color: '#666' },
  segmented: { flexDirection: 'row', gap: 6, flexWrap: 'wrap' },
  segment: { paddingVertical: 8, paddingHorizontal: 10, borderRadius: 8, borderWidth: 1, borderColor: '#ccc' },
  segmentActive: { backgroundColor: '#2563eb', borderColor: '#2563eb' },
  segmentText: { color: '#333', fontSize: 13, fontWeight: '600' },
  segmentTextActive: { color: '#fff' },
  error: { color: 'red' },
  actions: { gap: 8, marginTop: 4 },
  primaryButton: { backgroundColor: '#2563eb', borderRadius: 8, paddingVertical: 12, alignItems: 'center' },
  primaryText: { color: '#fff', fontWeight: '600' },
  secondaryButton: { borderRadius: 8, paddingVertical: 12, alignItems: 'center' },
  secondaryText: { color: '#2563eb', fontWeight: '600' },
  deleteButton: { borderRadius: 8, paddingVertical: 12, alignItems: 'center' },
  deleteText: { color: '#dc2626', fontWeight: '600' },
});
