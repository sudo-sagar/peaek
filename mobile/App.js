import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Linking,
  Modal,
  RefreshControl,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
// Import SafeAreaProvider and SafeAreaView to protect against notches and status bars
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';

const API_BASE = 'https://peaek.onrender.com';
const PER_CATEGORY = 3;

const CATEGORIES = [
  { id: 'all', label: 'All', emoji: '🔥' },
  { id: '23', label: 'Comedy', emoji: '😂' },
  { id: '24', label: 'Entertainment', emoji: '🎬' },
  { id: '20', label: 'Gaming', emoji: '🎮' },
  { id: '17', label: 'Sports', emoji: '⚽' },
  { id: '10', label: 'Music', emoji: '🎵' },
  { id: '1', label: 'Film', emoji: '🎥' },
  { id: '2', label: 'Autos', emoji: '🚗' },
  { id: '15', label: 'Pets', emoji: '🐶' },
  { id: '18', label: 'Short Movies', emoji: '🍿' },
  { id: '19', label: 'Travel', emoji: '✈️' },
  { id: '22', label: 'Vlogs', emoji: '📹' },
  { id: '25', label: 'News', emoji: '📰' },
  { id: '26', label: 'Howto', emoji: '🍳' },
  { id: '27', label: 'Education', emoji: '🎓' },
  { id: '28', label: 'Tech', emoji: '🔬' },
];

const CATEGORY_ORDER = ['23', '24', '20', '17', '10', '1', '2', '15', '18', '19', '22', '25', '26', '27', '28'];

export default function App() {
  const [cards, setCards] = useState([]);
  const [activeCategory, setActiveCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const [deviceId, setDeviceId] = useState(null);
  const [userCount, setUserCount] = useState(null);

  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');
  const [feedbackStatus, setFeedbackStatus] = useState(null);

  useEffect(() => {
    (async () => {
      let id = await AsyncStorage.getItem('device_id');
      if (!id) {
        id =
          'dev_' +
          Math.random().toString(36).substring(2) +
          Date.now().toString(36);
        await AsyncStorage.setItem('device_id', id);
      }
      setDeviceId(id);

      try {
        await fetch(`${API_BASE}/api/users/ping`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ device_id: id, app_version: '1.0.0' }),
        });
      } catch (e) {
        // silent
      }

      try {
        const res = await fetch(`${API_BASE}/api/users/count`);
        if (res.ok) {
          const data = await res.json();
          setUserCount(data);
        }
      } catch (e) {
        // silent
      }
    })();
  }, []);

  const fetchCards = useCallback(async (category, isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);

      const url =
        category === 'all'
          ? `${API_BASE}/api/cards?limit=100`
          : `${API_BASE}/api/cards?limit=50&category=${category}`;

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 20000); // 20s for Render cold starts

      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setCards(data);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchCards(activeCategory);
  }, [activeCategory, fetchCards]);

  const onTabPress = (catId) => {
    if (catId === activeCategory) return;
    setActiveCategory(catId);
  };

  const openVideo = (videoId) => {
    if (!videoId) return;
    Linking.openURL(`https://www.youtube.com/watch?v=${videoId}`);
  };

  const onShare = async () => {
    try {
      await Share.share({
        message: 'Check out Peaek! It shows the funniest comments from trending YouTube videos. Download the app here: https://drive.google.com/file/d/1kwBg9aKZdcQX-eunXBGUmv0kdkbQsCeS/view?usp=drivesdk',
      });
    } catch (error) {
      console.log('Error sharing:', error.message);
    }
  };

  const formatNumber = (n) => {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
    if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
    return String(n);
  };

  const groupedByCategory = useMemo(() => {
    if (activeCategory !== 'all') {
      return [
        {
          category: activeCategory,
          items: cards.slice(0, PER_CATEGORY),
        },
      ];
    }

    const groups = {};
    cards.forEach((c) => {
      const cat = c.video_category || 'other';
      if (!groups[cat]) groups[cat] = [];
      if (groups[cat].length < PER_CATEGORY) groups[cat].push(c);
    });

    return CATEGORY_ORDER.filter((cat) => groups[cat]).map((cat) => ({
      category: cat,
      items: groups[cat],
    }));
  }, [cards, activeCategory]);

  const submitFeedback = async () => {
    const text = feedbackText.trim();

    if (text.length < 3) {
      setFeedbackStatus('error');
      return;
    }

    setFeedbackStatus('sending');

    try {
      const res = await fetch(`${API_BASE}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: deviceId, text }),
      });

      if (!res.ok) throw new Error('send failed');

      setFeedbackStatus('sent');
      setFeedbackText('');

      setTimeout(() => {
        setFeedbackOpen(false);
        setFeedbackStatus(null);
      }, 1200);
    } catch (e) {
      setFeedbackStatus('error');
    }
  };

  const renderCard = (item) => (
    <View key={item.id} style={styles.card}>
      <Text style={styles.label}>🎬 TOP YOUTUBE COMMENT</Text>

      <Text style={styles.commentText}>{item.comment_text}</Text>

      <View style={styles.metaRow}>
        <Text style={styles.metaText}>👍 {formatNumber(item.comment_likes)}</Text>
        <Text style={styles.metaText}>💬 {formatNumber(item.comment_reply_count)}</Text>
      </View>

      {item.comment_author && (
        <Text style={styles.authorText}>— {item.comment_author}</Text>
      )}

      <TouchableOpacity
        style={styles.revealButton}
        onPress={() => openVideo(item.video_id)}
        activeOpacity={0.85}
      >
        <Text style={styles.revealButtonText}>Reveal the video</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <SafeAreaProvider>
      {/* SafeAreaView protects the top (clock) and bottom (home bar) */}
      <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
        <View style={styles.header}>
          <Text style={styles.appName}>Peaek</Text>
          {userCount && userCount.total > 0 && (
            <Text style={styles.userCount}>👥 {userCount.total.toLocaleString()}</Text>
          )}
        </View>

        <View style={styles.tabsWrapper}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.tabsContent}
          >
            {CATEGORIES.map((cat) => {
              const isActive = activeCategory === cat.id;
              return (
                <TouchableOpacity
                  key={cat.id}
                  style={[styles.tab, isActive && styles.tabActive]}
                  onPress={() => onTabPress(cat.id)}
                >
                  <Text style={[styles.tabText, isActive && styles.tabTextActive]}>
                    {cat.emoji} {cat.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </ScrollView>
        </View>

        {loading ? (
          <View style={styles.center}>
            <ActivityIndicator size="large" color="#ff4500" />
            <Text style={styles.loadingText}>Loading...</Text>
          </View>
        ) : error ? (
          <View style={styles.center}>
            <Text style={styles.errorEmoji}>📡</Text>
            <Text style={styles.errorTitle}>Couldn't load cards</Text>
            <Text style={styles.errorText}>{error}</Text>
            <TouchableOpacity
              style={styles.retryBtn}
              onPress={() => fetchCards(activeCategory)}
            >
              <Text style={styles.retryText}>Try again</Text>
            </TouchableOpacity>
          </View>
        ) : groupedByCategory.length === 0 ? (
          <View style={styles.center}>
            <Text style={styles.errorEmoji}>😴</Text>
            <Text style={styles.errorTitle}>Nothing here yet</Text>
            <Text style={styles.errorText}>
              No top comments in this category right now. Try another tab.
            </Text>
          </View>
        ) : (
          <FlatList
            data={groupedByCategory}
            keyExtractor={(item) => item.category}
            renderItem={({ item: group }) => {
              const cat = CATEGORIES.find((c) => c.id === group.category);
              return (
                <View>
                  <Text style={styles.sectionHeader}>
                    {cat?.emoji || '📺'} {cat?.label || 'Other'}
                  </Text>
                  {group.items.map((card) => renderCard(card))}
                </View>
              );
            }}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.listContent}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={() => fetchCards(activeCategory, true)}
                tintColor="#ff4500"
              />
            }
          />
        )}

        {/* Fixed Bottom Bar inside SafeAreaView */}
        <View style={styles.bottomBar}>
          <TouchableOpacity 
            style={styles.bottomBtn} 
            onPress={onShare} 
            activeOpacity={0.7}
          >
            <Text style={styles.bottomBtnText}>📤 Share</Text>
          </TouchableOpacity>
          
          <TouchableOpacity 
            style={styles.bottomBtn} 
            onPress={() => {
              setFeedbackStatus(null);
              setFeedbackOpen(true);
            }} 
            activeOpacity={0.7}
          >
            <Text style={styles.bottomBtnText}>💬 Feedback</Text>
          </TouchableOpacity>
        </View>

        <Modal
          visible={feedbackOpen}
          animationType="slide"
          transparent
          onRequestClose={() => setFeedbackOpen(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalBox}>
              <Text style={styles.modalTitle}>Send Feedback</Text>
              <Text style={styles.modalSubtitle}>
                What's working? What's broken? What do you want to see?
              </Text>

              <TextInput
                style={styles.feedbackInput}
                placeholder="Type your feedback..."
                placeholderTextColor="#999"
                value={feedbackText}
                onChangeText={setFeedbackText}
                multiline
                maxLength={2000}
                editable={feedbackStatus !== 'sending'}
              />

              {feedbackStatus === 'sent' && (
                <Text style={styles.feedbackSuccess}>✅ Thanks — got it.</Text>
              )}
              {feedbackStatus === 'error' && (
                <Text style={styles.feedbackError}>
                  Couldn't send. Check your connection and try again.
                </Text>
              )}

              <View style={styles.modalActions}>
                <TouchableOpacity
                  style={styles.modalCancel}
                  onPress={() => {
                    setFeedbackOpen(false);
                    setFeedbackStatus(null);
                  }}
                  disabled={feedbackStatus === 'sending'}
                >
                  <Text style={styles.modalCancelText}>Cancel</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={styles.modalSend}
                  onPress={submitFeedback}
                  disabled={feedbackStatus === 'sending'}
                >
                  <Text style={styles.modalSendText}>
                    {feedbackStatus === 'sending' ? 'Sending...' : 'Send'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f2f2f2' },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 8,
    backgroundColor: '#ffffff',
  },
  appName: {
    fontSize: 26,
    fontWeight: '900',
    color: '#000000',
    letterSpacing: -0.5,
  },
  userCount: {
    fontSize: 13,
    fontWeight: '700',
    color: '#666',
  },

  tabsWrapper: {
    borderBottomWidth: 1,
    borderBottomColor: '#e8e8e8',
    backgroundColor: '#ffffff',
  },
  tabsContent: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    alignItems: 'center',
  },
  tab: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    borderWidth: 1,
    borderColor: '#e0e0e0',
    marginRight: 8,
  },
  tabActive: { backgroundColor: '#ff4500', borderColor: '#ff4500' },
  tabText: { color: '#333333', fontSize: 13, fontWeight: '700' },
  tabTextActive: { color: '#ffffff' },

  listContent: { padding: 16, paddingBottom: 20 },

  sectionHeader: {
    color: '#000',
    fontSize: 20,
    fontWeight: '900',
    marginTop: 12,
    marginBottom: 12,
    letterSpacing: -0.3,
  },

  card: {
    backgroundColor: '#ffffff',
    borderRadius: 18,
    padding: 20,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#e8e8e8',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 6,
    elevation: 2,
  },
  label: {
    color: '#ff0000',
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginBottom: 14,
  },
  commentText: {
    color: '#000000',
    fontSize: 17,
    lineHeight: 25,
    fontWeight: '500',
    marginBottom: 16,
  },
  metaRow: { flexDirection: 'row', marginBottom: 8 },
  metaText: {
    color: '#666',
    fontSize: 13,
    fontWeight: '600',
    marginRight: 18,
  },
  authorText: { color: '#999', fontSize: 12, marginBottom: 16 },
  revealButton: {
    backgroundColor: '#ff4500',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 6,
  },
  revealButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '800',
    letterSpacing: 0.3,
  },

  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f2f2f2',
    padding: 24,
  },
  loadingText: { color: '#666', marginTop: 12, fontSize: 14 },
  errorEmoji: { fontSize: 44, marginBottom: 12 },
  errorTitle: { color: '#000', fontSize: 20, fontWeight: '900', marginBottom: 8 },
  errorText: {
    color: '#666',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 20,
    maxWidth: 280,
  },
  retryBtn: {
    backgroundColor: '#ff4500',
    paddingHorizontal: 24,
    paddingVertical: 10,
    borderRadius: 8,
  },
  retryText: { color: '#ffffff', fontWeight: '700' },

  bottomBar: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e8e8e8',
    paddingVertical: 12,
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.05,
    shadowRadius: 5,
  },
  bottomBtn: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  bottomBtnText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#333333',
  },

  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    justifyContent: 'flex-end',
  },
  modalBox: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 24,
    paddingBottom: 36,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '900',
    color: '#000',
    marginBottom: 6,
  },
  modalSubtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 16,
    lineHeight: 20,
  },
  feedbackInput: {
    backgroundColor: '#f7f7f7',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    padding: 14,
    minHeight: 120,
    fontSize: 15,
    color: '#000',
    textAlignVertical: 'top',
  },
  feedbackSuccess: {
    color: '#1a7a32',
    fontSize: 14,
    fontWeight: '700',
    marginTop: 12,
  },
  feedbackError: {
    color: '#c92b00',
    fontSize: 14,
    fontWeight: '700',
    marginTop: 12,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 20,
  },
  modalCancel: {
    paddingHorizontal: 18,
    paddingVertical: 12,
    marginRight: 8,
  },
  modalCancelText: { color: '#666', fontSize: 15, fontWeight: '700' },
  modalSend: {
    backgroundColor: '#ff4500',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 10,
  },
  modalSendText: { color: '#ffffff', fontSize: 15, fontWeight: '900' },
});