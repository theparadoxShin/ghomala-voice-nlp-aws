/**
 * NAM SA' — Main App
 * "Le soleil s'est levé"
 * Ghomala' Language Preservation AI
 */

import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { LanguageProvider } from './src/context/LanguageContext';
import HomeScreen from './src/screens/HomeScreen';
import DictionaryScreen from './src/screens/DictionaryScreen';
import LiveScreen from './src/screens/LiveScreen';
import DialogueScreen from './src/screens/DialogueScreen';
import ProverbsScreen from './src/screens/ProverbsScreen';
import TutorScreen from './src/screens/TutorScreen';
import { Colors } from './src/theme';

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <LanguageProvider>
      <NavigationContainer>
        <StatusBar style="dark" />
        <Stack.Navigator
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: Colors.background },
            animation: 'slide_from_right',
          }}
        >
          <Stack.Screen name="Home" component={HomeScreen} />
          <Stack.Screen name="Dictionary" component={DictionaryScreen} />
          <Stack.Screen
            name="Dialogue"
            component={LiveScreen}
            options={{ animation: 'slide_from_bottom' }}
          />
          <Stack.Screen name="Chat" component={DialogueScreen} />
          <Stack.Screen name="Proverbs" component={ProverbsScreen} />
          <Stack.Screen name="Tutor" component={TutorScreen} />
        </Stack.Navigator>
      </NavigationContainer>
    </LanguageProvider>
  );
}
