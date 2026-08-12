import { useEffect, useState } from 'react';
import { ActivityIndicator, SafeAreaView, StyleSheet, Text, View } from 'react-native';

const API_URL = process.env.EXPO_PUBLIC_API_URL;

type HealthStatus = {
  database: string;
  postgis: string;
  pgvector: string;
  redis: string;
};

export default function App() {
  const [status, setStatus] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((res) => res.json())
      .then(setStatus)
      .catch((err) => setError(String(err)));
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.title}>Conexão com o backend</Text>
      <Text style={styles.url}>{API_URL}</Text>

      {error && <Text style={styles.error}>Erro: {error}</Text>}
      {!status && !error && <ActivityIndicator />}
      {status && (
        <View style={styles.statusBox}>
          {Object.entries(status).map(([key, value]) => (
            <Text key={key} style={styles.statusLine}>
              {key}: {String(value)}
            </Text>
          ))}
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24, gap: 12 },
  title: { fontSize: 20, fontWeight: '600' },
  url: { color: '#666' },
  error: { color: 'red' },
  statusBox: { gap: 4, alignItems: 'flex-start' },
  statusLine: { fontFamily: 'monospace' },
});
