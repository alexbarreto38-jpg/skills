import {
  Armchair,
  Box,
  Footprints,
  Gem,
  Home,
  Lamp,
  PanelTop,
  Scissors,
  Shirt,
  Square,
  Type,
  User,
  Volume2,
} from "lucide-react";

export function EntityIcon({ type, subtype, className = "size-3.5" }: { type: string; subtype?: string | null; className?: string }) {
  switch (type) {
    case "character":
      return <User className={className} />;
    case "hair":
      return <Scissors className={className} />;
    case "wardrobe":
      return subtype === "footwear" ? <Footprints className={className} /> : <Shirt className={className} />;
    case "accessory":
      return <Gem className={className} />;
    case "furniture":
      return <Armchair className={className} />;
    case "environment":
      return <Home className={className} />;
    case "environment_part":
      return subtype === "window" || subtype === "window_view" ? <PanelTop className={className} /> : <Square className={className} />;
    case "lighting":
      return <Lamp className={className} />;
    case "text":
      return <Type className={className} />;
    case "audio":
      return <Volume2 className={className} />;
    default:
      return <Box className={className} />;
  }
}
