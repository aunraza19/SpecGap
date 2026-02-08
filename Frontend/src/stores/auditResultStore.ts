import { create } from 'zustand';
import type { Flashcard, CouncilSessionResponse, FullSpectrumResponse } from '@/types/api';

interface AuditResultState {
    // Response data
    response: CouncilSessionResponse | FullSpectrumResponse | null;
    flashcards: Flashcard[];

    // User interaction state
    acceptedCards: Flashcard[];
    rejectedCards: Flashcard[];
    currentCardIndex: number;

    // Actions
    setResponse: (response: CouncilSessionResponse | FullSpectrumResponse) => void;
    acceptCard: (card: Flashcard) => void;
    rejectCard: (card: Flashcard) => void;
    nextCard: () => void;
    previousCard: () => void;
    resetCards: () => void;
    clearResults: () => void;
}

export const useAuditResultStore = create<AuditResultState>((set, get) => ({
    response: null,
    flashcards: [],
    acceptedCards: [],
    rejectedCards: [],
    currentCardIndex: 0,

    setResponse: (response) => {
        const flashcards = response.council_verdict?.flashcards || [];
        set({
            response,
            flashcards,
            acceptedCards: [],
            rejectedCards: [],
            currentCardIndex: 0,
        });
    },

    acceptCard: (card) => {
        const { acceptedCards, currentCardIndex, flashcards } = get();
        if (!acceptedCards.find(c => c.id === card.id)) {
            set({
                acceptedCards: [...acceptedCards, card],
                currentCardIndex: Math.min(currentCardIndex + 1, flashcards.length - 1),
            });
        }
    },

    rejectCard: (card) => {
        const { rejectedCards, currentCardIndex, flashcards } = get();
        if (!rejectedCards.find(c => c.id === card.id)) {
            set({
                rejectedCards: [...rejectedCards, card],
                currentCardIndex: Math.min(currentCardIndex + 1, flashcards.length - 1),
            });
        }
    },

    nextCard: () => {
        const { currentCardIndex, flashcards } = get();
        if (currentCardIndex < flashcards.length - 1) {
            set({ currentCardIndex: currentCardIndex + 1 });
        }
    },

    previousCard: () => {
        const { currentCardIndex } = get();
        if (currentCardIndex > 0) {
            set({ currentCardIndex: currentCardIndex - 1 });
        }
    },

    resetCards: () => {
        set({
            acceptedCards: [],
            rejectedCards: [],
            currentCardIndex: 0,
        });
    },

    clearResults: () => {
        set({
            response: null,
            flashcards: [],
            acceptedCards: [],
            rejectedCards: [],
            currentCardIndex: 0,
        });
    },
}));
