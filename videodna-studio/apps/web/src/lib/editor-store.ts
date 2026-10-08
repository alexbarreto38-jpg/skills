import { create } from "zustand";

/** Client-only editor state (selection, playback). Server state lives in React Query. */
export interface EditorState {
  selectedKey: string | null;
  selectedShot: string | null;
  currentTime: number;
  seekRequest: { time: number; nonce: number } | null;
  showBoxes: boolean;
  activeCategory: string | null;
  select: (key: string | null) => void;
  selectShot: (shotId: string | null) => void;
  setTime: (time: number) => void;
  seek: (time: number) => void;
  toggleBoxes: () => void;
  setCategory: (category: string | null) => void;
  reset: () => void;
}

export const useEditor = create<EditorState>((set) => ({
  selectedKey: null,
  selectedShot: null,
  currentTime: 0,
  seekRequest: null,
  showBoxes: true,
  activeCategory: null,
  select: (key) => set({ selectedKey: key, activeCategory: null }),
  selectShot: (shotId) => set({ selectedShot: shotId }),
  setTime: (time) => set({ currentTime: time }),
  seek: (time) => set({ seekRequest: { time, nonce: Math.random() }, currentTime: time }),
  toggleBoxes: () => set((s) => ({ showBoxes: !s.showBoxes })),
  setCategory: (category) => set({ activeCategory: category }),
  reset: () =>
    set({ selectedKey: null, selectedShot: null, currentTime: 0, seekRequest: null, activeCategory: null }),
}));
