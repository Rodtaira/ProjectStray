import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, SafeAreaView, StyleSheet, Text, TouchableOpacity } from 'react-native';

import { LoginScreen } from './LoginScreen';
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
    <SafeAreaView style={styles.center}>
      <Text style={styles.title}>Logado como {user.full_name ?? user.email}</Text>
      <Text>{user.email}</Text>
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>Sair</Text>
      </TouchableOpacity>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 8, padding: 24 },
  title: { fontSize: 18, fontWeight: '600' },
  logoutButton: { marginTop: 16, padding: 10 },
  logoutText: { color: '#2563eb', fontWeight: '600' },
});
