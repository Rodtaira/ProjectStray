import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { CampaignDetailModal } from './CampaignDetailModal';
import { CreateCampaignModal } from './CreateCampaignModal';
import { Campaign, CampaignCreate, createCampaign, listCampaigns } from './lib/api';
import { authenticatedFetch } from './lib/auth-client';

const STATUS_LABELS: Record<string, string> = {
  active: 'Ativa',
  funded: 'Meta atingida',
  completed: 'Concluída',
  cancelled: 'Cancelada',
};

export function CampaignsScreen() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);

  const loadCampaigns = useCallback(async () => {
    try {
      const data = await listCampaigns();
      setCampaigns(data);
    } catch {
      // lista vazia se falhar
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCampaigns();
  }, [loadCampaigns]);

  async function handleCreateCampaign(data: CampaignCreate) {
    const newCampaign = await authenticatedFetch((token) => createCampaign(token, data));
    setCampaigns((prev) => [newCampaign, ...prev]);
    setModalVisible(false);
  }

  return (
    <View style={styles.container}>
      {loading ? (
        <ActivityIndicator style={styles.center} />
      ) : (
        <FlatList
          data={campaigns}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          ListEmptyComponent={<Text style={styles.empty}>Nenhuma campanha ainda.</Text>}
          renderItem={({ item }) => (
            <TouchableOpacity style={styles.card} onPress={() => setSelectedCampaign(item)}>
              <Text style={styles.cardTitle}>{item.title}</Text>
              <Text style={styles.cardGoal}>Meta: R$ {parseFloat(item.goal_amount).toFixed(2)}</Text>
              <View
                style={[styles.badge, item.status === 'active' ? styles.badgeActive : styles.badgeOther]}
              >
                <Text style={styles.badgeText}>{STATUS_LABELS[item.status] ?? item.status}</Text>
              </View>
            </TouchableOpacity>
          )}
        />
      )}

      <TouchableOpacity style={styles.fab} onPress={() => setModalVisible(true)}>
        <Text style={styles.fabText}>+</Text>
      </TouchableOpacity>

      <CreateCampaignModal
        visible={modalVisible}
        onCancel={() => setModalVisible(false)}
        onSubmit={handleCreateCampaign}
      />

      {selectedCampaign && (
        <CampaignDetailModal campaign={selectedCampaign} onClose={() => setSelectedCampaign(null)} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, justifyContent: 'center' },
  list: { padding: 16, gap: 10 },
  empty: { textAlign: 'center', color: '#666', marginTop: 40 },
  card: { backgroundColor: '#f5f5f5', borderRadius: 10, padding: 14, gap: 6 },
  cardTitle: { fontSize: 16, fontWeight: '600' },
  cardGoal: { color: '#666' },
  badge: { alignSelf: 'flex-start', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 10 },
  badgeActive: { backgroundColor: '#dbeafe' },
  badgeOther: { backgroundColor: '#e5e7eb' },
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
