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

import { Sighting, SightingUpdate } from './lib/api';

type Props = {
  sighting: Sighting;
  currentUserId: string;
  onClose: () => void;
  onUpdate: (id: string, changes: SightingUpdate) => Promise<void>;
};

export function SightingDetailModal({ sighting, currentUserId, onClose, onUpdate }: Props) {
  const [editing, setEditing] = useState(false);
  const [description, setDescription] = useState(sighting.description ?? '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isOwner = sighting.reporter_id === currentUserId;
  const isResolved = sighting.status === 'resolved';

  async function handleSaveDescription() {
    setLoading(true);
    setError(null);
    try {
      await onUpdate(sighting.id, { description: description.trim() });
      setEditing(false);
    } catch {
      setError('Não foi possível salvar.');
    } finally {
      setLoading(false);
    }
  }

  async function handleToggleResolved() {
    setLoading(true);
    setError(null);
    try {
      await onUpdate(sighting.id, { status: isResolved ? 'open' : 'resolved' });
    } catch {
      setError('Não foi possível atualizar o status.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal visible animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <View style={styles.header}>
            <View style={[styles.badge, isResolved ? styles.badgeResolved : styles.badgeOpen]}>
              <Text style={styles.badgeText}>{isResolved ? 'Resolvido' : 'Em aberto'}</Text>
            </View>
            <TouchableOpacity onPress={onClose}>
              <Text style={styles.closeText}>Fechar</Text>
            </TouchableOpacity>
          </View>

          {editing ? (
            <TextInput
              style={styles.input}
              value={description}
              onChangeText={setDescription}
              multiline
              autoFocus
            />
          ) : (
            <Text style={styles.description}>{sighting.description || 'Sem descrição'}</Text>
          )}

          <Text style={styles.meta}>
            Relatado em {new Date(sighting.created_at).toLocaleDateString('pt-BR')}
          </Text>

          {error && <Text style={styles.error}>{error}</Text>}

          {isOwner && (
            <View style={styles.actions}>
              {editing ? (
                <TouchableOpacity
                  style={styles.primaryButton}
                  onPress={handleSaveDescription}
                  disabled={loading}
                >
                  {loading ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <Text style={styles.primaryText}>Salvar descrição</Text>
                  )}
                </TouchableOpacity>
              ) : (
                <TouchableOpacity style={styles.secondaryButton} onPress={() => setEditing(true)}>
                  <Text style={styles.secondaryText}>Editar descrição</Text>
                </TouchableOpacity>
              )}

              <TouchableOpacity
                style={styles.primaryButton}
                onPress={handleToggleResolved}
                disabled={loading}
              >
                <Text style={styles.primaryText}>
                  {isResolved ? 'Reabrir' : 'Marcar como resolvido'}
                </Text>
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
  card: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    padding: 24,
    gap: 12,
  },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  badgeOpen: { backgroundColor: '#fee2e2' },
  badgeResolved: { backgroundColor: '#dcfce7' },
  badgeText: { fontSize: 12, fontWeight: '600' },
  closeText: { color: '#2563eb', fontWeight: '600' },
  description: { fontSize: 16 },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  meta: { color: '#666', fontSize: 13 },
  error: { color: 'red' },
  actions: { gap: 8, marginTop: 8 },
  primaryButton: {
    backgroundColor: '#2563eb',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  primaryText: { color: '#fff', fontWeight: '600' },
  secondaryButton: { borderRadius: 8, paddingVertical: 12, alignItems: 'center' },
  secondaryText: { color: '#2563eb', fontWeight: '600' },
});
