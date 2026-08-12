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

type Props = {
  visible: boolean;
  onCancel: () => void;
  onSubmit: (description: string) => Promise<void>;
};

export function CreateSightingModal({ visible, onCancel, onSubmit }: Props) {
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    setError(null);
    setLoading(true);
    try {
      await onSubmit(description.trim());
      setDescription('');
    } catch {
      setError('Não foi possível salvar o relato. Tente de novo.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <Text style={styles.title}>Novo relato</Text>
          <Text style={styles.subtitle}>Vai ser registrado na sua localização atual</Text>

          <TextInput
            style={styles.input}
            placeholder="Ex: cachorro caramelo, parece perdido"
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
  card: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    padding: 24,
    gap: 12,
  },
  title: { fontSize: 18, fontWeight: '700' },
  subtitle: { color: '#666', marginBottom: 8 },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  error: { color: 'red' },
  actions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 12, marginTop: 8 },
  cancelButton: { padding: 12 },
  cancelText: { color: '#666', fontWeight: '600' },
  submitButton: { backgroundColor: '#2563eb', borderRadius: 8, paddingVertical: 12, paddingHorizontal: 20 },
  submitText: { color: '#fff', fontWeight: '600' },
});
