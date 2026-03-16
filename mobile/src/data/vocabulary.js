/**
 * Vocabulaire pour le mode Tuteur.
 * Les traductions Ghomala' sont chargées via l'API /api/translate.
 * Organisation : 3 niveaux × 5 thèmes × ~5 mots.
 */

export const LEVELS = [
  {
    id: 'basic',
    titleKey: 'basic',
    color: '#2D7A3A',
    icon: '🌱',
    topics: [
      {
        id: 'greetings',
        titleKey: 'greetings',
        emoji: '👋',
        words: [
          { emoji: '👋', fr: 'Bonjour', en: 'Hello' },
          { emoji: '👋', fr: 'Bonsoir', en: 'Good evening' },
          { emoji: '🙏', fr: 'Merci', en: 'Thank you' },
          { emoji: '😊', fr: 'S\'il te plaît', en: 'Please' },
          { emoji: '👋', fr: 'Au revoir', en: 'Goodbye' },
          { emoji: '✅', fr: 'Oui', en: 'Yes' },
          { emoji: '❌', fr: 'Non', en: 'No' },
        ],
      },
      {
        id: 'numbers',
        titleKey: 'numbers',
        emoji: '🔢',
        words: [
          { emoji: '1️⃣', fr: 'Un', en: 'One' },
          { emoji: '2️⃣', fr: 'Deux', en: 'Two' },
          { emoji: '3️⃣', fr: 'Trois', en: 'Three' },
          { emoji: '4️⃣', fr: 'Quatre', en: 'Four' },
          { emoji: '5️⃣', fr: 'Cinq', en: 'Five' },
          { emoji: '🔟', fr: 'Dix', en: 'Ten' },
        ],
      },
      {
        id: 'family',
        titleKey: 'familyMembers',
        emoji: '👨‍👩‍👧‍👦',
        words: [
          { emoji: '👨', fr: 'Père', en: 'Father' },
          { emoji: '👩', fr: 'Mère', en: 'Mother' },
          { emoji: '👶', fr: 'Enfant', en: 'Child' },
          { emoji: '👦', fr: 'Frère', en: 'Brother' },
          { emoji: '👧', fr: 'Sœur', en: 'Sister' },
        ],
      },
      {
        id: 'animals',
        titleKey: 'animals',
        emoji: '🐾',
        words: [
          { emoji: '🐎', fr: 'Cheval', en: 'Horse' },
          { emoji: '🐕', fr: 'Chien', en: 'Dog' },
          { emoji: '🐐', fr: 'Chèvre', en: 'Goat' },
          { emoji: '🐔', fr: 'Poule', en: 'Chicken' },
          { emoji: '🐍', fr: 'Serpent', en: 'Snake' },
        ],
      },
      {
        id: 'food',
        titleKey: 'food',
        emoji: '🍽️',
        words: [
          { emoji: '💧', fr: 'Eau', en: 'Water' },
          { emoji: '🫘', fr: 'Manioc', en: 'Cassava' },
          { emoji: '🍌', fr: 'Plantain', en: 'Plantain' },
          { emoji: '🌴', fr: 'Huile de palme', en: 'Palm oil' },
          { emoji: '🍚', fr: 'Riz', en: 'Rice' },
        ],
      },
    ],
  },
  {
    id: 'intermediate',
    titleKey: 'intermediate',
    color: '#E8A020',
    icon: '🌿',
    topics: [
      {
        id: 'colors',
        titleKey: 'colors',
        emoji: '🎨',
        words: [
          { emoji: '⬛', fr: 'Noir', en: 'Black' },
          { emoji: '⬜', fr: 'Blanc', en: 'White' },
          { emoji: '🟥', fr: 'Rouge', en: 'Red' },
          { emoji: '🟩', fr: 'Vert', en: 'Green' },
          { emoji: '🟨', fr: 'Jaune', en: 'Yellow' },
        ],
      },
      {
        id: 'body',
        titleKey: 'body',
        emoji: '🧍',
        words: [
          { emoji: '👤', fr: 'Tête', en: 'Head' },
          { emoji: '👁️', fr: 'Œil', en: 'Eye' },
          { emoji: '👂', fr: 'Oreille', en: 'Ear' },
          { emoji: '🤚', fr: 'Main', en: 'Hand' },
          { emoji: '🦶', fr: 'Pied', en: 'Foot' },
          { emoji: '❤️', fr: 'Cœur', en: 'Heart' },
        ],
      },
      {
        id: 'market',
        titleKey: 'market',
        emoji: '🏪',
        words: [
          { emoji: '💰', fr: 'Argent', en: 'Money' },
          { emoji: '🛒', fr: 'Acheter', en: 'To buy' },
          { emoji: '📦', fr: 'Vendre', en: 'To sell' },
          { emoji: '⚖️', fr: 'Combien ?', en: 'How much?' },
          { emoji: '🏠', fr: 'Maison', en: 'House' },
        ],
      },
      {
        id: 'time',
        titleKey: 'time',
        emoji: '⏰',
        words: [
          { emoji: '☀️', fr: 'Jour', en: 'Day' },
          { emoji: '🌙', fr: 'Nuit', en: 'Night' },
          { emoji: '🌅', fr: 'Matin', en: 'Morning' },
          { emoji: '🌇', fr: 'Soir', en: 'Evening' },
          { emoji: '📅', fr: 'Aujourd\'hui', en: 'Today' },
          { emoji: '📅', fr: 'Demain', en: 'Tomorrow' },
        ],
      },
      {
        id: 'actions',
        titleKey: 'actions',
        emoji: '🏃',
        words: [
          { emoji: '🍽️', fr: 'Manger', en: 'To eat' },
          { emoji: '💧', fr: 'Boire', en: 'To drink' },
          { emoji: '🚶', fr: 'Marcher', en: 'To walk' },
          { emoji: '💬', fr: 'Parler', en: 'To speak' },
          { emoji: '👂', fr: 'Écouter', en: 'To listen' },
          { emoji: '📧', fr: 'Envoyer', en: 'To send' },
        ],
      },
    ],
  },
  {
    id: 'advanced',
    titleKey: 'advanced',
    color: '#7A2E1E',
    icon: '🌳',
    topics: [
      {
        id: 'tones',
        titleKey: 'tones',
        emoji: '🎵',
        words: [
          { emoji: '⬆️', fr: 'Ton haut (á)', en: 'High tone (á)' },
          { emoji: '⬇️', fr: 'Ton bas (à)', en: 'Low tone (à)' },
          { emoji: '↗️', fr: 'Ton montant (ǎ)', en: 'Rising tone (ǎ)' },
          { emoji: '↘️', fr: 'Ton descendant (â)', en: 'Falling tone (â)' },
        ],
      },
      {
        id: 'grammar',
        titleKey: 'grammar',
        emoji: '📝',
        words: [
          { emoji: '👤', fr: 'Je / Moi', en: 'I / Me' },
          { emoji: '👥', fr: 'Nous', en: 'We' },
          { emoji: '🫵', fr: 'Toi / Tu', en: 'You' },
          { emoji: '👫', fr: 'Ils / Elles', en: 'They' },
        ],
      },
      {
        id: 'expressions',
        titleKey: 'expressions',
        emoji: '💬',
        words: [
          { emoji: '❓', fr: 'Comment tu t\'appelles ?', en: 'What is your name?' },
          { emoji: '📍', fr: 'D\'où viens-tu ?', en: 'Where are you from?' },
          { emoji: '💪', fr: 'Je vais bien', en: 'I am fine' },
          { emoji: '🤷', fr: 'Je ne comprends pas', en: 'I don\'t understand' },
          { emoji: '🔄', fr: 'Répète s\'il te plaît', en: 'Please repeat' },
        ],
      },
      {
        id: 'culture',
        titleKey: 'culture',
        emoji: '🎭',
        words: [
          { emoji: '👑', fr: 'Chef / Roi', en: 'Chief / King' },
          { emoji: '🏡', fr: 'Village', en: 'Village' },
          { emoji: '🪘', fr: 'Tambour', en: 'Drum' },
          { emoji: '💃', fr: 'Danse', en: 'Dance' },
          { emoji: '🎉', fr: 'Fête', en: 'Celebration' },
        ],
      },
      {
        id: 'ceremonies',
        titleKey: 'ceremonies',
        emoji: '🎊',
        words: [
          { emoji: '💒', fr: 'Mariage', en: 'Wedding' },
          { emoji: '👶', fr: 'Naissance', en: 'Birth' },
          { emoji: '🌾', fr: 'Récolte', en: 'Harvest' },
          { emoji: '🙏', fr: 'Prière', en: 'Prayer' },
          { emoji: '🤝', fr: 'Alliance', en: 'Alliance' },
        ],
      },
    ],
  },
];
