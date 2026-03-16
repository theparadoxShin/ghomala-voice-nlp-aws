import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Localization from 'expo-localization';

const LANG_KEY = 'namsa_language';

const translations = {
  fr: {
    appSubtitle: "Le soleil s'est levé",
    appDescription: "Préservons le Ghomala' ensemble",
    translate: 'Traduire',
    translateSub: 'Dictionnaire & Traduction',
    dialogue: 'Dialogue',
    dialogueSub: 'Conversation Live Audio',
    proverbs: 'Proverbes',
    proverbsSub: 'Sagesse Bamiléké',
    tutor: 'Tuteur',
    tutorSub: "Apprendre le Ghomala'",
    tapToSpeak: 'Appuie pour parler',
    typeMessage: 'Écris ton message...',
    send: 'Envoyer',
    from: 'De',
    to: 'Vers',
    translateAction: 'Traduire',
    listen: 'Écouter',
    categories: 'Catégories',
    meaning: 'Signification',
    basic: 'Basique',
    intermediate: 'Intermédiaire',
    advanced: 'Avancé',
    back: 'Retour',
    welcome: 'Bienvenue',
    liveConversation: 'Conversation en direct avec NAM SA\'',
    askAbout: 'Demander à NAM SA\'',
    noTranslation: 'Tape du texte ci-dessus',
    error: 'Erreur de connexion',
    loading: 'Chargement...',
    translateToGhomala: "Traduire en Ghomala'",
    tapToTranslate: 'Appuie pour traduire',
    frenchLabel: 'Français',
    englishLabel: 'English',
    ghomalaLabel: "Ghomala'",
    proverbMeaning: 'Ce que ça veut dire',
    learnMore: 'En savoir plus',
    topicWords: 'mots',
    startLesson: 'Commencer',
    congratulations: 'Bravo !',
    wisdom: 'Sagesse',
    family: 'Famille & Communauté',
    courage: 'Courage & Persévérance',
    nature: 'Nature & Vie',
    community: 'Solidarité',
    education: 'Éducation & Savoir',
    greetings: 'Salutations',
    numbers: 'Nombres',
    familyMembers: 'La Famille',
    animals: 'Animaux',
    food: 'Nourriture',
    colors: 'Couleurs',
    body: 'Corps Humain',
    market: 'Au Marché',
    time: 'Le Temps',
    actions: 'Actions',
    tones: 'Les Tons',
    grammar: 'Grammaire',
    expressions: 'Expressions',
    culture: 'Culture',
    ceremonies: 'Cérémonies',
    chatMode: 'Chat textuel →',
  },
  en: {
    appSubtitle: 'The sun has risen',
    appDescription: "Let's preserve Ghomala' together",
    translate: 'Translate',
    translateSub: 'Dictionary & Translation',
    dialogue: 'Dialogue',
    dialogueSub: 'Live Audio Conversation',
    proverbs: 'Proverbs',
    proverbsSub: 'Bamiléké Wisdom',
    tutor: 'Tutor',
    tutorSub: "Learn Ghomala'",
    tapToSpeak: 'Tap to speak',
    typeMessage: 'Type your message...',
    send: 'Send',
    from: 'From',
    to: 'To',
    translateAction: 'Translate',
    listen: 'Listen',
    categories: 'Categories',
    meaning: 'Meaning',
    basic: 'Basic',
    intermediate: 'Intermediate',
    advanced: 'Advanced',
    back: 'Back',
    welcome: 'Welcome',
    liveConversation: 'Live conversation with NAM SA\'',
    askAbout: 'Ask NAM SA\'',
    noTranslation: 'Type text above',
    error: 'Connection error',
    loading: 'Loading...',
    translateToGhomala: "Translate to Ghomala'",
    tapToTranslate: 'Tap to translate',
    frenchLabel: 'Français',
    englishLabel: 'English',
    ghomalaLabel: "Ghomala'",
    proverbMeaning: 'What it means',
    learnMore: 'Learn more',
    topicWords: 'words',
    startLesson: 'Start',
    congratulations: 'Well done!',
    wisdom: 'Wisdom',
    family: 'Family & Community',
    courage: 'Courage & Perseverance',
    nature: 'Nature & Life',
    community: 'Solidarity',
    education: 'Education & Knowledge',
    greetings: 'Greetings',
    numbers: 'Numbers',
    familyMembers: 'Family',
    animals: 'Animals',
    food: 'Food',
    colors: 'Colors',
    body: 'Human Body',
    market: 'At the Market',
    time: 'Time',
    actions: 'Actions',
    tones: 'Tones',
    grammar: 'Grammar',
    expressions: 'Expressions',
    culture: 'Culture',
    ceremonies: 'Ceremonies',
    chatMode: 'Text chat →',
  },
};

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState('fr');
  const [ready, setReady] = useState(false);

  useEffect(() => {
    (async () => {
      const stored = await AsyncStorage.getItem(LANG_KEY);
      if (stored === 'en' || stored === 'fr') {
        setLang(stored);
      } else {
        // Detect device language
        const deviceLangs = Localization.getLocales();
        const deviceLang = deviceLangs?.[0]?.languageCode;
        if (deviceLang === 'en') setLang('en');
      }
      setReady(true);
    })();
  }, []);

  const switchLanguage = async (newLang) => {
    setLang(newLang);
    await AsyncStorage.setItem(LANG_KEY, newLang);
  };

  const t = (key) => translations[lang]?.[key] || translations.fr[key] || key;

  if (!ready) return null;

  return (
    <LanguageContext.Provider value={{ lang, switchLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export const useLanguage = () => useContext(LanguageContext);
