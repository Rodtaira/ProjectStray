import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Modal,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import * as WebBrowser from 'expo-web-browser';

import { Campaign, Donation, createDonation, listCampaignDonations } from './lib/api';
import { authenticatedFetch } from './lib/auth-client';

type Props = {
  campaign: Campaign;
  onClose: () => void;
};

const STATUS_LABELS: Record<string, string> = {
  active: 'Ativa',
  funded: 'Meta atingida',
  completed: 'Concluída',
  cancelled: 'Cancelada',
};

const PRESET_AMOUNTS = [10, 25, 50, 100];

export function CampaignDetailModal({ campaign, onClose }: Props) {
  const [donations, setDonations] = useState<Donation[]>([]);
  const [loadingDonations, setLoadingDonations] = useState(true);
  const [amount, setAmount] = useState('');
  const [donating, setDonating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDonations = useCallback(async () => {
    setLoadingDonations(true);
    try {
      const data = await listCampaignDonations(campaign.id);
      setDonations(data);
    } catch {
      // segue sem o extrato se falhar
    } finally {
      setLoadingDonations(false);
    }
  }, [campaign.id]);

  useEffect(() => {
    loadDonations();
  }, [loadDonations]);

  const goal = parseFloat(campaign.goal_amount);
  const raised = donations.reduce((sum, d) => sum + parseFloat(d.amount), 0);
  const progress = goal > 0 ? Math.min(raised / goal, 1) : 0;

  async function handleDonate() {
    setError(null);
    const parsedAmount = parseFloat(amount.replace(',', '.'));
    if (!parsedAmount || parsedAmount <= 0) {
      setError('Digite um valor válido.');
      return;
    }

    setDonating(true);
    try {
      const { checkout_url } = await authenticatedFetch((token) =>
        createDonation(token, campaign.id, parsedAmount)
      );
      await WebBrowser.openBrowserAsync(checkout_url);
      setAmount('');
      // O webhook pode levar alguns segundos pra confirmar — isso pode não
      // pegar a doação nova ainda. O botão "Atualizar" no extrato resolve.
      await loadDonations();
    } catch {
      setError('Não foi possível iniciar o pagamento. Tente de novo.');
    } finally {
      setDonating(false);
    }
  }

  return (
    <Modal visible animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.card}>
          <View style={styles.header}>
            <Text style={styles.title}>{campaign.title}</Text>
            <TouchableOpacity onPress={onClose}>
              <Text style={styles.closeText}>Fechar</Text>
            </TouchableOpacity>
          </View>

          <Text style={styles.statusText}>{STATUS_LABELS[campaign.status] ?? campaign.status}</Text>

          {campaign.description && <Text style={styles.description}>{campaign.description}</Text>}

          <View style={styles.progressBarBg}>
            <View style={[styles.progressBarFill, { width: `${progress * 100}%` }]} />
          </View>
          <Text style={styles.progressText}>
            R$ {raised.toFixed(2)} arrecadados de R$ {goal.toFixed(2)}
          </Text>

          {campaign.status === 'active' && (
            <View style={styles.donateBox}>
              <Text style={styles.label}>Fazer uma doação</Text>

              <View style={styles.presetRow}>
                {PRESET_AMOUNTS.map((v) => (
                  <TouchableOpacity
                    key={v}
                    style={styles.presetChip}
                    onPress={() => setAmount(String(v))}
                  >
                    <Text style={styles.presetText}>R$ {v}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <TextInput
                style={styles.input}
                placeholder="Outro valor em R$"
                value={amount}
                onChangeText={setAmount}
                keyboardType="decimal-pad"
              />
              {error && <Text style={styles.error}>{error}</Text>}
              <TouchableOpacity style={styles.donateButton} onPress={handleDonate} disabled={donating}>
                {donating ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.donateText}>Doar</Text>
                )}
              </TouchableOpacity>
            </View>
          )}

          <View style={styles.ledgerHeader}>
            <Text style={styles.label}>Doações confirmadas</Text>
            <TouchableOpacity onPress={loadDonations}>
              <Text style={styles.refreshText}>Atualizar</Text>
            </TouchableOpacity>
          </View>

          {loadingDonations ? (
            <ActivityIndicator size="small" />
          ) : donations.length === 0 ? (
            <Text style={styles.emptyLedger}>Nenhuma doação confirmada ainda.</Text>
          ) : (
            donations.slice(0, 5).map((d) => (
              <Text key={d.id} style={styles.ledgerLine}>
                R$ {parseFloat(d.amount).toFixed(2)} — {new Date(d.created_at).toLocaleDateString('pt-BR')}
              </Text>
            ))
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
    gap: 8,
    maxHeight: '85%',
  },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { fontSize: 18, fontWeight: '700', flexShrink: 1 },
  closeText: { color: '#2563eb', fontWeight: '600' },
  statusText: { color: '#666', fontSize: 13 },
  description: { fontSize: 15 },
  progressBarBg: { height: 10, backgroundColor: '#e5e7eb', borderRadius: 6, overflow: 'hidden', marginTop: 4 },
  progressBarFill: { height: '100%', backgroundColor: '#22c55e' },
  progressText: { color: '#666', fontSize: 13 },
  label: { fontSize: 13, color: '#666', fontWeight: '600' },
  donateBox: { gap: 8, marginTop: 8 },
  presetRow: { flexDirection: 'row', gap: 8 },
  presetChip: {
    borderWidth: 1,
    borderColor: '#2563eb',
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  presetText: { color: '#2563eb', fontWeight: '600', fontSize: 13 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 12 },
  error: { color: 'red' },
  donateButton: { backgroundColor: '#2563eb', borderRadius: 8, paddingVertical: 12, alignItems: 'center' },
  donateText: { color: '#fff', fontWeight: '600' },
  ledgerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  refreshText: { color: '#2563eb', fontWeight: '600', fontSize: 13 },
  emptyLedger: { color: '#999', fontSize: 13 },
  ledgerLine: { color: '#444', fontSize: 13 },
});
