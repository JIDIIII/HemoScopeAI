import { useState } from "react";
import { Modal, Pressable, Text, View } from "react-native";
import { ChevronDown, FlaskConical, Check } from "lucide-react-native";
import { USE_MOCK_API } from "@/constants/api";
import {
  getMockScenario,
  setMockScenario,
  mockScenarios,
  type MockScenario,
} from "@/services/api/mock";
import { colors, typography } from "@/theme";
export function DemoControls({ onChange }: { onChange?: () => void }) {
  const [value, setValue] = useState(getMockScenario);
  const [open, setOpen] = useState(false);
  if (!USE_MOCK_API) return null;
  const choose = (next: MockScenario) => {
    setMockScenario(next);
    setValue(next);
    setOpen(false);
    onChange?.();
  };
  return (
    <>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Choose simulated API scenario"
        onPress={() => setOpen(true)}
        style={{
          borderWidth: 1,
          borderStyle: "dashed",
          borderColor: "#99BFC7",
          backgroundColor: "#F1F7F8",
          borderRadius: 13,
          padding: 12,
          flexDirection: "row",
          gap: 10,
          alignItems: "center",
        }}
      >
        <FlaskConical size={18} color={colors.navy} />
        <View style={{ flex: 1 }}>
          <Text style={{ fontSize: 11, color: colors.navy, fontWeight: "600" }}>
            Demo controls
          </Text>
          <Text style={[typography.caption, { fontSize: 9 }]}>
            Choose a simulated API response
          </Text>
        </View>
        <Text style={{ fontSize: 10, color: colors.navy }}>
          {value.replaceAll("_", " ")}
        </Text>
        <ChevronDown size={16} color={colors.navy} />
      </Pressable>
      <Modal
        visible={open}
        transparent
        animationType="fade"
        onRequestClose={() => setOpen(false)}
      >
        <View
          style={{
            flex: 1,
            backgroundColor: "#102D4777",
            justifyContent: "center",
            padding: 26,
          }}
        >
          <View
            style={{ backgroundColor: "white", padding: 20, borderRadius: 20 }}
          >
            <Text style={typography.sectionTitle}>Simulated API response</Text>
            {mockScenarios.map((item) => (
              <Pressable
                accessibilityRole="button"
                key={item}
                onPress={() => choose(item)}
                style={{
                  paddingVertical: 13,
                  flexDirection: "row",
                  justifyContent: "space-between",
                }}
              >
                <Text style={typography.body}>{item.replaceAll("_", " ")}</Text>
                {value === item ? (
                  <Check color={colors.teal} size={18} />
                ) : null}
              </Pressable>
            ))}
            <Pressable
              accessibilityRole="button"
              onPress={() => setOpen(false)}
              style={{ paddingVertical: 12 }}
            >
              <Text style={{ color: colors.teal }}>Cancel</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </>
  );
}
