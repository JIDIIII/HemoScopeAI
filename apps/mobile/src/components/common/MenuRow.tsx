import { ChevronRight, type LucideIcon } from "lucide-react-native";
import { Pressable, Text, View } from "react-native";
import { colors, typography } from "@/theme";
export function MenuRow({
  icon: Icon,
  title,
  subtitle,
  onPress,
}: {
  icon: LucideIcon;
  title: string;
  subtitle: string;
  onPress?: () => void;
}) {
  return (
    <Pressable
      accessibilityRole={onPress ? "button" : undefined}
      onPress={onPress}
      disabled={!onPress}
      style={{
        flexDirection: "row",
        alignItems: "center",
        gap: 12,
        padding: 13,
        minHeight: 62,
        borderBottomWidth: 1,
        borderColor: "#EDF2F4",
      }}
    >
      <View
        style={{
          width: 36,
          height: 36,
          borderRadius: 11,
          backgroundColor: colors.lightGray,
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Icon size={19} color="#527D94" />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={{ color: colors.navy, fontSize: 12, fontWeight: "600" }}>
          {title}
        </Text>
        <Text style={[typography.caption, { fontSize: 10, marginTop: 3 }]}>
          {subtitle}
        </Text>
      </View>
      {onPress ? <ChevronRight size={17} color={colors.navy} /> : null}
    </Pressable>
  );
}
