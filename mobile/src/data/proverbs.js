/**
 * Proverbes Bamiléké / Camerounais
 * Organisés par catégorie thématique.
 * Les traductions Ghomala' sont obtenues via l'API.
 */

export const PROVERB_CATEGORIES = [
  {
    id: 'wisdom',
    emoji: '✨',
    titleKey: 'wisdom',
    color: '#E8A020',
    proverbs: [
      {
        id: 'w1',
        fr: "La parole est comme l'eau : une fois versée, on ne la ramasse plus.",
        en: 'Words are like water: once spilled, they cannot be gathered back.',
        meaningFr: 'Réfléchis avant de parler, car les mots ont du poids.',
        meaningEn: 'Think before you speak, for words carry weight.',
      },
      {
        id: 'w2',
        fr: "L'arbre ne tombe pas au premier coup de hache.",
        en: 'The tree does not fall with the first axe blow.',
        meaningFr: 'La persévérance est la clé du succès.',
        meaningEn: 'Perseverance is the key to success.',
      },
      {
        id: 'w3',
        fr: 'Celui qui ne sait pas d\'où il vient ne peut pas savoir où il va.',
        en: 'Those who do not know where they come from cannot know where they are going.',
        meaningFr: 'Connais tes racines pour tracer ton avenir.',
        meaningEn: 'Know your roots to chart your future.',
      },
      {
        id: 'w4',
        fr: 'La vérité est comme le soleil, on ne peut pas la cacher avec la main.',
        en: 'Truth is like the sun, you cannot hide it with your hand.',
        meaningFr: 'La vérité finit toujours par éclater.',
        meaningEn: 'The truth always comes to light.',
      },
    ],
  },
  {
    id: 'family',
    emoji: '👨‍👩‍👧‍👦',
    titleKey: 'family',
    color: '#7A2E1E',
    proverbs: [
      {
        id: 'f1',
        fr: "L'enfant qui se lave les mains mange à la table des aînés.",
        en: 'The child who washes their hands eats at the table of elders.',
        meaningFr: 'Le respect et la discipline ouvrent toutes les portes.',
        meaningEn: 'Respect and discipline open all doors.',
      },
      {
        id: 'f2',
        fr: 'Un seul doigt ne peut pas laver le visage.',
        en: 'A single finger cannot wash the face.',
        meaningFr: "L'union fait la force dans la famille.",
        meaningEn: 'Unity makes strength in the family.',
      },
      {
        id: 'f3',
        fr: 'La mère est le pilier de la case.',
        en: 'The mother is the pillar of the home.',
        meaningFr: 'La mère est le fondement de toute famille.',
        meaningEn: 'The mother is the foundation of every family.',
      },
      {
        id: 'f4',
        fr: "Quand le père parle, l'enfant écoute ; quand l'enfant grandit, le père observe.",
        en: 'When the father speaks, the child listens; when the child grows, the father observes.',
        meaningFr: 'L\'éducation est un dialogue entre les générations.',
        meaningEn: 'Education is a dialogue between generations.',
      },
    ],
  },
  {
    id: 'courage',
    emoji: '💪',
    titleKey: 'courage',
    color: '#A0522D',
    proverbs: [
      {
        id: 'c1',
        fr: "C'est au bout de la patience qu'on trouve le ciel.",
        en: "It's at the end of patience that you find heaven.",
        meaningFr: 'La patience mène aux plus grandes récompenses.',
        meaningEn: 'Patience leads to the greatest rewards.',
      },
      {
        id: 'c2',
        fr: 'Celui qui a peur de la pluie ne traversera jamais la rivière.',
        en: 'He who fears the rain will never cross the river.',
        meaningFr: 'Le courage est nécessaire pour avancer dans la vie.',
        meaningEn: 'Courage is necessary to move forward in life.',
      },
      {
        id: 'c3',
        fr: 'Le soleil ne se couche pas sans nouvelles.',
        en: 'The sun does not set without news.',
        meaningFr: 'Chaque jour apporte ses leçons et opportunités.',
        meaningEn: 'Every day brings its lessons and opportunities.',
      },
    ],
  },
  {
    id: 'nature',
    emoji: '🌿',
    titleKey: 'nature',
    color: '#2D7A3A',
    proverbs: [
      {
        id: 'n1',
        fr: "L'eau qui coule ne remonte pas la colline.",
        en: 'Flowing water does not go back up the hill.',
        meaningFr: 'Le temps passé ne revient pas, vis pleinement.',
        meaningEn: 'Time past does not return, live fully.',
      },
      {
        id: 'n2',
        fr: 'Quand la lune brille, les étoiles ne se cachent pas.',
        en: 'When the moon shines, the stars do not hide.',
        meaningFr: 'Il y a de la place pour tous dans la grandeur.',
        meaningEn: 'There is room for everyone in greatness.',
      },
      {
        id: 'n3',
        fr: "La terre ne ment jamais : ce que tu sèmes, tu le récoltes.",
        en: 'The earth never lies: what you sow, you shall reap.',
        meaningFr: 'Nos actions ont toujours des conséquences.',
        meaningEn: 'Our actions always have consequences.',
      },
    ],
  },
  {
    id: 'community',
    emoji: '🤝',
    titleKey: 'community',
    color: '#5A9EC8',
    proverbs: [
      {
        id: 's1',
        fr: "Un seul bras ne peut pas attacher un paquet.",
        en: 'A single arm cannot tie a bundle.',
        meaningFr: "L'entraide est indispensable dans la communauté.",
        meaningEn: 'Mutual aid is essential in the community.',
      },
      {
        id: 's2',
        fr: 'La force du crocodile, c\'est l\'eau.',
        en: "The crocodile's strength is the water.",
        meaningFr: 'Chacun brille là où il se sent chez lui.',
        meaningEn: 'Everyone shines where they feel at home.',
      },
      {
        id: 's3',
        fr: "Quand les fourmis s'unissent, elles transportent un éléphant.",
        en: 'When ants unite, they carry an elephant.',
        meaningFr: "L'union de la communauté accomplit l'impossible.",
        meaningEn: 'Community unity accomplishes the impossible.',
      },
    ],
  },
  {
    id: 'education',
    emoji: '📚',
    titleKey: 'education',
    color: '#9E4A3A',
    proverbs: [
      {
        id: 'e1',
        fr: 'Qui veut apprendre demande ; qui sait déjà enseigne.',
        en: 'Those who want to learn ask; those who know teach.',
        meaningFr: "L'apprentissage est un cycle continu de partage.",
        meaningEn: 'Learning is a continuous cycle of sharing.',
      },
      {
        id: 'e2',
        fr: 'Le savoir est une arme qui ne rouille pas.',
        en: 'Knowledge is a weapon that never rusts.',
        meaningFr: "L'éducation est le trésor le plus durable.",
        meaningEn: 'Education is the most lasting treasure.',
      },
      {
        id: 'e3',
        fr: "L'œil du maître engraisse le cheval.",
        en: "The master's eye fattens the horse.",
        meaningFr: "L'attention et la supervision produisent l'excellence.",
        meaningEn: 'Attention and supervision produce excellence.',
      },
    ],
  },
];
