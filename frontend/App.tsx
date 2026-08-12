import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, SafeAreaView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { LoginScreen } from './LoginScreen';
import { MapScreen } from './MapScreen';
import { UserMe, getMe } from './lib/api';
import { authenticatedFetch, onSessionExpired } from './lib/auth-client';
import { clearTokens } from './lib/auth-storage';

export default function App() {
  const [checkingSession, setCheckingSession] = useState(true);
  const [user, setUser] = useState<UserMe | null>(null);

  const loadUser = useCallback(async () => {
    try {
      const u = await authenticatedFetch((token) => getMe(token));
      setUser(u);
    } catch {
      setUser(null);
    } finally {
      setCheckingSession(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    return onSessionExpired(() => {
      setUser(null);
      setCheckingSession(false);
    });
  }, []);

  async function handleLogout() {
    await clearTokens();
    setUser(null);
  }

  if (checkingSession) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator />
      </SafeAreaView>
    );
  }

  if (!user) {
    return <LoginScreen onLoginSuccess={loadUser} />;
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerText}>{user.full_name ?? user.email}</Text>
        <TouchableOpacity onPress={handleLogout}>
          <Text style={styles.logoutText}>Sair</Text>
        </TouchableOpacity>
      </View>
      <MapScreen currentUserId={user.id} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#ddd',
  },
  headerText: { fontSize: 16, fontWeight: '600' },
  logoutText: { color: '#2563eb', fontWeight: '600' },
});
