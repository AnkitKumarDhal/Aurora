import { View, Text, StyleSheet } from "react-native";

export default function ConversationScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Conversation Screen</Text>
      <Text>Adaptive quesitoning UI goes here</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 24,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#fff",
  },
  title: {
    fontSize: 22,
    fontWeight: "bold",
    marginBottom: 12,
  },
});
