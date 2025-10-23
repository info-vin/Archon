import { createContext } from 'react';
import { SettingsContextType } from './SettingsContext';

export const SettingsContext = createContext<SettingsContextType | undefined>(undefined);
